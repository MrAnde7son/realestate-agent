#!/bin/bash
python3 -m gis.mcp_server  &
python3 -m yad2.mcp_server  &
python3 -m gov.mcp_server  &
python3 -m mavat.mcp_server  &
