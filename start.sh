#!/bin/bash
export $(grep -v '^#' .env | xargs)
uvicorn convocapp_agent.main:app --host 0.0.0.0 --port 5000 --reload
