#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
from datetime import date,timedelta,datetime

from schedule import every, repeat
from sentry_sdk import capture_exception
from influxdb_client import Point
import influxdb_exporter

from sdk_enedis.api import API
enedis = API(
    os.environ.get("ENEDIS_CLIENT_ID"),
    os.environ.get("ENEDIS_CLIENT_SECRET")
)

def fetch():
    today = date.today() - timedelta(days=1)
    delta = timedelta(days=7)

    points = []

    try:
        for year in range(3):
            start = today.replace(year=today.year - year)
            for releve in enedis.daily_consumption(
                os.environ.get("PDL"),
                from_date=(start - delta).isoformat(),
                to_date=(start).isoformat()
            ):
                conso = releve["consommation"]
                points.append(Point("enedis")
                    .time(datetime.fromisoformat(conso["date_fin_consommation"]).replace(year=today.year))
                    .tag("year", start.year)
                    .field("energy", conso["energie"])
                )

    except Exception as e:
        capture_exception(e)

    return points

@repeat(every(12).hours)
def enedis_exporter():
    points = fetch()
    for point in points:
        influxdb_exporter.InfluxDB().push(point)
