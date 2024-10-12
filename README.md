# Really Awesome Display of Meteorologic / Atmospheric Things (RADMAT)

![Build badge](/aliask/radmat/actions/workflows/build/badge.svg?branch=main)

RADMAT is designed to fetch the latest rain radar images from the Australian Bureau of Meteorology (BoM) for display on an [LED Matrix](/aliask/ledmatrix).

## Overview

The Bureau of Meteorology provides rain radar information which is popular in Melbourne (and possibly other cities). A phrase like "it's not raining unless the BoM shows it" is not unheard of.

The BoM website displays this data like this:

![BoM Radar Animation](images/bom-radar.gif)

It's a cold day in the middle of winter today, and you can see the small clouds heading Northwards and bringing cold air up from Antarctica. Better grab that jacket.

This project aims to replicate this useful information away from a PC. Plus it just looks nice.

## Details

### 1. Download Raw Data

Downloads the latest images from the BoM FTP server (ftp.bom.gov.au). They look like this:

<img src="images/frame.png" width="320">

### 2. Prepare Fames

These images are then cropped and resized to fit the size of the LED Matrix (16x32 pixels)

<img src="images/frame-resized.png" width="320">

### 3. Send Data

The resized frames are sent to the `ledserver` utility in the custom ledmatrix data format.

## Usage

A docker compose file is provided to run the radmat service. It will download the latest images from the BOM FTP server, resize them to fit the LED Matrix, and send them to the LEDServer.

To run the radmat service:

```bash
docker compose up -d
```

The radmat service will run in the background, refreshing the images every 5 minutes.

To stop the radmat service:

```bash
docker compose down
```

## Configuration

The radmat service can be configured using environment variables.

| Variable | Description | Default |
| --- | --- | --- |
| `LEDSERVER_PORT` | The port to send the LEDMatrix data to | `20304` |
| `LEDSERVER_HOST` | The host to send the LEDMatrix data to | `127.0.0.1` |
| `RADAR_ID` | The ID of the radar to download images for. Visit [this page](http://www.bom.gov.au/australia/radar/) to see the IDs of other sites. | `IDR023` |
