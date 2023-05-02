# Import the dependencies.
from flask import Flask, jsonify
from datetime import datetime, timedelta
from sqlalchemy import create_engine, func
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.automap import automap_base
import numpy as np
import datetime as dt

#################################################
# Database Setup
#################################################

# reflect an existing database into a new model
engine = create_engine("sqlite:///../Resources/hawaii.sqlite")
Base = automap_base()

# reflect the tables
Base.prepare(engine, reflect=True)

# Save references to each table
measurement = Base.classes.measurement
station = Base.classes.station

# Create our session (link) from Python to the DB

Session = sessionmaker(bind=engine)
session = Session()

#################################################
# Flask Setup
#################################################

app = Flask(__name__)

@app.route("/")

def home():
    return (
        f"Welcome to the Climate App API!<br/><br/>"
        f"Available Routes:<br/>"
        f"/api/v1.0/precipitation<br/>"
        f"/api/v1.0/stations<br/>"
        f"/api/v1.0/tobs<br/>"
        f"/api/v1.0/start<br/>"
        f"/api/v1.0/start/end"
    )

#Define route precipitation

@app.route("/api/v1.0/precipitation")
def precipitation():
    # Calculate the date 1 year ago from the last data point in the database
    last_date = session.query(measurement.date).order_by(measurement.date.desc()).first()[0]
    year_ago = (datetime.strptime(last_date, '%Y-%m-%d') - timedelta(days=365)).strftime('%Y-%m-%d')
    
    # Query the precipitation data for the last 12 months and convert to a dictionary
    results = session.query(measurement.date, measurement.prcp).filter(measurement.date >= year_ago).all()
    prcp_dict = {}
    for date, prcp in results:
        prcp_dict[date] = prcp
    
    session.close()

    return jsonify(prcp_dict)

#Define route stations

@app.route("/api/v1.0/stations")
def stations():
    # query station names
    Station = Base.classes.station
    station_names = session.query(Station.station).all()

    # convert station names to list
    stations_list = list(np.ravel(station_names))

    session.close()

    # return list as JSON
    return jsonify(stations_list)

#Define route tobs

@app.route("/api/v1.0/tobs")
def tobs():
    # Query the most active station
    most_active_station = session.query(measurement.station)\
        .group_by(measurement.station)\
        .order_by(func.count().desc())\
        .first()[0]
    
    # Calculate the date 1 year ago from the last data point in the database
    last_date = session.query(measurement.date)\
        .filter(measurement.station == most_active_station)\
        .order_by(measurement.date.desc())\
        .first()[0]
    year_ago = dt.datetime.strptime(last_date, "%Y-%m-%d") - dt.timedelta(days=365)
    
    # Query the temperature observations for the previous year for the most active station
    temp_results = session.query(measurement.date, measurement.tobs)\
        .filter(measurement.station == most_active_station)\
        .filter(measurement.date >= year_ago)\
        .all()
    
    # Create a list of dictionaries for the temperature observations
    temp_list = []
    for date, temp in temp_results:
        temp_dict = {}
        temp_dict["date"] = date
        temp_dict["tobs"] = temp
        temp_list.append(temp_dict)

    session.close()
    return jsonify(temp_list)


#Define route for min, avg and max from a start date
@app.route("/api/v1.0/<start>")
def temperature_stats_start(start):
    # Query temperature stats for a start date and store in a dictionary
    results = session.query(func.min(measurement.tobs), func.avg(measurement.tobs), func.max(measurement.tobs)).\
        filter(measurement.date >= start).all()
    temperature_stats = {'TMIN': results[0][0], 'TAVG': results[0][1], 'TMAX': results[0][2]}

    session.close()
    return jsonify(temperature_stats)


#Define route for min, avg and max from a start date to a end date

@app.route("/api/v1.0/<start>/<end>")
def temperature_stats_range(start, end):
    # Query temperature stats for a range of dates and store in a dictionary
    results = session.query(func.min(measurement.tobs), func.avg(measurement.tobs), func.max(measurement.tobs)).\
        filter(measurement.date >= start).filter(measurement.date <= end).all()
    temperature_stats = {'TMIN': results[0][0], 'TAVG': results[0][1], 'TMAX': results[0][2]}

    session.close()
    return jsonify(temperature_stats)


if __name__ == "__main__":
    app.run(debug=True)

