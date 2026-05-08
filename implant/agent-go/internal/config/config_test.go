package config

import (
	"os"
	"path/filepath"
	"testing"
)

func TestLoadConfigAppliesDefaults(t *testing.T) {
	path := writeConfig(t, `{
		"agent_id": "agent-test-1",
		"server_url": "http://127.0.0.1:8000"
	}`)

	cfg, err := Load(path)
	if err != nil {
		t.Fatalf("Load returned error: %v", err)
	}
	if cfg.AgentID != "agent-test-1" {
		t.Fatalf("unexpected agent id: %s", cfg.AgentID)
	}
	if cfg.PollIntervalSeconds != defaultPollIntervalSeconds {
		t.Fatalf("unexpected poll interval: %d", cfg.PollIntervalSeconds)
	}
	if cfg.TimeoutSeconds != defaultTimeoutSeconds {
		t.Fatalf("unexpected timeout: %d", cfg.TimeoutSeconds)
	}
	if cfg.Metadata == nil {
		t.Fatal("metadata should be initialized")
	}
}

func TestLoadConfigRequiresAgentID(t *testing.T) {
	path := writeConfig(t, `{"server_url": "http://127.0.0.1:8000"}`)

	_, err := Load(path)
	if err == nil {
		t.Fatal("expected validation error")
	}
}

func writeConfig(t *testing.T, body string) string {
	t.Helper()
	path := filepath.Join(t.TempDir(), "agent.json")
	if err := os.WriteFile(path, []byte(body), 0o600); err != nil {
		t.Fatalf("write config: %v", err)
	}
	return path
}
