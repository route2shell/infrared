package config

import (
	"encoding/json"
	"errors"
	"fmt"
	"net/url"
	"os"
)

const (
	defaultPollIntervalSeconds = 5
	defaultTimeoutSeconds      = 10
)

type Config struct {
	AgentID             string            `json:"agent_id"`
	ServerURL           string            `json:"server_url"`
	PollIntervalSeconds int               `json:"poll_interval_seconds"`
	TimeoutSeconds      int               `json:"timeout_seconds"`
	Metadata            map[string]string `json:"metadata"`
}

func Load(path string) (Config, error) {
	raw, err := os.ReadFile(path)
	if err != nil {
		return Config{}, err
	}

	var cfg Config
	if err := json.Unmarshal(raw, &cfg); err != nil {
		return Config{}, fmt.Errorf("parse config: %w", err)
	}

	cfg.applyDefaults()
	if err := cfg.Validate(); err != nil {
		return Config{}, err
	}
	return cfg, nil
}

func (cfg *Config) applyDefaults() {
	if cfg.PollIntervalSeconds == 0 {
		cfg.PollIntervalSeconds = defaultPollIntervalSeconds
	}
	if cfg.TimeoutSeconds == 0 {
		cfg.TimeoutSeconds = defaultTimeoutSeconds
	}
	if cfg.Metadata == nil {
		cfg.Metadata = map[string]string{}
	}
}

func (cfg Config) Validate() error {
	if cfg.AgentID == "" {
		return errors.New("agent_id is required")
	}
	if cfg.ServerURL == "" {
		return errors.New("server_url is required")
	}
	parsed, err := url.Parse(cfg.ServerURL)
	if err != nil {
		return fmt.Errorf("server_url is invalid: %w", err)
	}
	if parsed.Scheme != "http" && parsed.Scheme != "https" {
		return errors.New("server_url must use http or https")
	}
	if parsed.Host == "" {
		return errors.New("server_url must include a host")
	}
	if cfg.PollIntervalSeconds < 1 {
		return errors.New("poll_interval_seconds must be at least 1")
	}
	if cfg.TimeoutSeconds < 1 {
		return errors.New("timeout_seconds must be at least 1")
	}
	return nil
}
