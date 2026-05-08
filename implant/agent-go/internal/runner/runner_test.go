package runner

import (
	"context"
	"strings"
	"testing"
)

func TestExecutorAllowsEcho(t *testing.T) {
	executor := New()

	result := executor.Run(context.Background(), "echo infrared v1")

	if result.Status != StatusCompleted {
		t.Fatalf("unexpected status: %s", result.Status)
	}
	if strings.TrimSpace(result.Stdout) != "infrared v1" {
		t.Fatalf("unexpected stdout: %q", result.Stdout)
	}
	if result.ExitCode != 0 {
		t.Fatalf("unexpected exit code: %d", result.ExitCode)
	}
}

func TestExecutorRejectsUnsupportedCommands(t *testing.T) {
	executor := New()

	result := executor.Run(context.Background(), "cat /etc/passwd")

	if result.Status != StatusFailed {
		t.Fatalf("unexpected status: %s", result.Status)
	}
	if result.ExitCode != 126 {
		t.Fatalf("unexpected exit code: %d", result.ExitCode)
	}
	if !strings.Contains(result.Stderr, "unsupported V1 command") {
		t.Fatalf("unexpected stderr: %q", result.Stderr)
	}
}

func TestExecutorAllowsPwd(t *testing.T) {
	executor := New()

	result := executor.Run(context.Background(), "pwd")

	if result.Status != StatusCompleted {
		t.Fatalf("unexpected status: %s", result.Status)
	}
	if strings.TrimSpace(result.Stdout) == "" {
		t.Fatal("expected pwd output")
	}
}
