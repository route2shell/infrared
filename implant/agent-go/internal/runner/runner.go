package runner

import (
	"context"
	"fmt"
	"os"
	"os/user"
	"strings"
)

const (
	StatusCompleted = "completed"
	StatusFailed    = "failed"
)

type Result struct {
	Stdout   string
	Stderr   string
	ExitCode int
	Status   string
}

type Executor interface {
	Run(ctx context.Context, command string) Result
}

type LocalExecutor struct{}

func New() LocalExecutor {
	return LocalExecutor{}
}

func (LocalExecutor) Run(ctx context.Context, command string) Result {
	select {
	case <-ctx.Done():
		return failed("task cancelled")
	default:
	}

	fields := strings.Fields(command)
	if len(fields) == 0 {
		return failed("empty command")
	}

	switch fields[0] {
	case "whoami":
		if len(fields) != 1 {
			return failed("whoami does not accept arguments in V1")
		}
		currentUser, err := user.Current()
		if err != nil {
			return failed(fmt.Sprintf("whoami failed: %v", err))
		}
		return completed(currentUser.Username)
	case "hostname":
		if len(fields) != 1 {
			return failed("hostname does not accept arguments in V1")
		}
		hostname, err := os.Hostname()
		if err != nil {
			return failed(fmt.Sprintf("hostname failed: %v", err))
		}
		return completed(hostname)
	case "pwd":
		if len(fields) != 1 {
			return failed("pwd does not accept arguments in V1")
		}
		wd, err := os.Getwd()
		if err != nil {
			return failed(fmt.Sprintf("pwd failed: %v", err))
		}
		return completed(wd)
	case "echo":
		return completed(strings.Join(fields[1:], " "))
	default:
		return Result{
			Stderr:   fmt.Sprintf("unsupported V1 command: %s", fields[0]),
			ExitCode: 126,
			Status:   StatusFailed,
		}
	}
}

func completed(stdout string) Result {
	if stdout != "" && !strings.HasSuffix(stdout, "\n") {
		stdout += "\n"
	}
	return Result{
		Stdout:   stdout,
		ExitCode: 0,
		Status:   StatusCompleted,
	}
}

func failed(stderr string) Result {
	return Result{
		Stderr:   stderr,
		ExitCode: 1,
		Status:   StatusFailed,
	}
}
