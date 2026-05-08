package client

import (
	"context"
	"encoding/json"
	"net/http"
	"net/http/httptest"
	"testing"
	"time"
)

func TestClientTaskingLifecycle(t *testing.T) {
	var resultPosted bool
	server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		w.Header().Set("Content-Type", "application/json")
		switch {
		case r.Method == http.MethodPost && r.URL.Path == "/api/agent/checkin":
			_ = json.NewEncoder(w).Encode(map[string]any{
				"session": map[string]any{
					"session_id": "sess-test-1",
					"agent_id":   "agent-test-1",
				},
			})
		case r.Method == http.MethodGet && r.URL.Path == "/api/agent/agent-test-1/tasks":
			_ = json.NewEncoder(w).Encode(map[string]any{
				"tasks": []map[string]any{
					{"task_id": 1, "command": "whoami", "status": "delivered"},
				},
			})
		case r.Method == http.MethodPost && r.URL.Path == "/api/agent/agent-test-1/results":
			resultPosted = true
			_ = json.NewEncoder(w).Encode(map[string]any{
				"task_id":   1,
				"status":    "completed",
				"exit_code": 0,
			})
		default:
			t.Fatalf("unexpected request: %s %s", r.Method, r.URL.Path)
		}
	}))
	defer server.Close()

	api := New(server.URL, time.Second)
	ctx := context.Background()

	session, err := api.CheckIn(ctx, CheckinRequest{AgentID: "agent-test-1"})
	if err != nil {
		t.Fatalf("CheckIn returned error: %v", err)
	}
	if session.SessionID != "sess-test-1" {
		t.Fatalf("unexpected session id: %s", session.SessionID)
	}

	tasks, err := api.Tasks(ctx, "agent-test-1")
	if err != nil {
		t.Fatalf("Tasks returned error: %v", err)
	}
	if len(tasks) != 1 || tasks[0].Command != "whoami" {
		t.Fatalf("unexpected tasks: %#v", tasks)
	}

	_, err = api.PostResult(ctx, "agent-test-1", ResultPostRequest{
		TaskID:   1,
		Stdout:   "user",
		ExitCode: 0,
		Status:   "completed",
	})
	if err != nil {
		t.Fatalf("PostResult returned error: %v", err)
	}
	if !resultPosted {
		t.Fatal("expected result post")
	}
}
