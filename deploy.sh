#!/bin/bash

gcloud functions deploy extract_strava_activities \
  --runtime python310 --trigger-http --allow-unauthenticated --entry-point extract_strava_activities \
  --set-env-vars GCP_PROJECT=automator-485711,STRAVA_SPREADSHEET_ID=1FeMOMpAUBlqlrMYX6S-eQEDp2f5tHLOHWMepV32lN0U \
  --region europe-central2
