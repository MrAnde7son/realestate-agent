#!/bin/bash
python3 -m gis.mcp.server &
python3 -m yad2.mcp.server &
python3 -m gov.mcp.server &