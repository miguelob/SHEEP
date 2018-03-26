"""
SQLAlchemy classes to describe the tables of benchmark measurements
"""

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy import Column, ForeignKey, Integer, String, Boolean, Float
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import create_engine
from sqlalchemy import and_, or_

import sqlite3

import os

#### the following regexes are only necessary for when we allow the user to
#### enter their own SQL query - shouldn't be there long-term!
import re
table_regex = re.compile("(FROM|from) ([\w]+)")
column_regex = re.compile("(SELECT|select) ([\*\w\,\s]+) (FROM|from)")

### this hard-coded location of an sqlite file is only necessary if we explicitly
### use sqlite3, which is in turn only necessary until we translate SQL queries into
### sqlalchemy commands

if "SHEEP_HOME" in os.environ.keys():
    DB_LOCATION = os.environ["SHEEP_HOME"]+"/frontend/sheep.db"
else:
    DB_LOCATION = os.environ["HOME"]+"/SHEEP/frontend/sheep.db"

    
Base = declarative_base()
##engine = create_engine("sqlite:///sheep.db")
engine = create_engine("sqlite:///"+DB_LOCATION)

class BenchmarkMeasurement(Base):
    __tablename__ = "benchmarks"
    id = Column(Integer, primary_key=True, autoincrement=True,nullable=False)
    context_name = Column(String(250), nullable=False)
    input_bitwidth = Column(Integer, nullable=False)
    input_signed = Column(Boolean, nullable=False)    
    gate_name = Column(String(250), nullable=False)
    depth = Column(Integer, nullable=False)
    num_slots = Column(Integer, nullable=False)
    tbb_enabled = Column(Boolean, nullable=True)
    parameters = Column(String(250), nullable=False)
    execution_time = Column(Float, nullable=False)
    is_correct = Column(Boolean, nullable=False)
    ciphertext_size = Column(Integer, nullable=True)
    private_key_size = Column(Integer, nullable=True)
    public_key_size = Column(Integer, nullable=True)        


class MidLevelBenchmark(Base):
    __tablename__ = "mid_level_benchmarks"
    id = Column(Integer, primary_key=True, autoincrement=True,nullable=False)
    context_name = Column(String(250), nullable=False)
    input_bitwidth = Column(Integer, nullable=False)
    input_signed = Column(Boolean, nullable=False)    
    circuit_name = Column(String(250), nullable=False)
    tbb_enabled = Column(Boolean, nullable=True)
    parameters = Column(String(250), nullable=False)
    execution_time = Column(Float, nullable=False)
    is_correct = Column(Boolean, nullable=False)
    ciphertext_size = Column(Integer, nullable=True)
    private_key_size = Column(Integer, nullable=True)
    public_key_size = Column(Integer, nullable=True)   
    
class CustomMeasurement(Base):
    __tablename__ = "circuit_tests"
    id = Column(Integer, primary_key=True, autoincrement=True,nullable=False)
    circuit_name = Column(String(250), nullable=False)
    num_inputs = Column(Integer, nullable=False)
    context_name = Column(String(250), nullable=False)
    input_type = Column(String(250), nullable=False)
    setup_time = Column(Float, nullable=False)
    encryption_time = Column(Float, nullable=False)
    evaluation_time = Column(Float, nullable=False)
    decryption_time = Column(Float, nullable=False)

    
Base.metadata.create_all(engine)

Base.metadata.bind = engine
DBSession = sessionmaker(bind=engine)
session = DBSession()

def get_table_and_columns(query):
    """
    parse the query to extract table name and columns
    """
    table_name = ""
    columns = []
    if table_regex.search(query):
        table_name = table_regex.search(query).groups()[1]
    if column_regex.search(query):
        columns = column_regex.search(query).groups()[1].split(",")
    return table_name, columns
        
def execute_query_sqlite3(query):
    """
    raw sql query
    """
    table,columns = get_table_and_columns(query)
    db = sqlite3.connect(DB_LOCATION)
    cursor = db.cursor()
    ### get the column headings, if e.g. '*' was used in the query
    if table and (len(columns) == 0 or columns[0] == "*"):
        cursor.execute("PRAGMA table_info("+table+");")
        columns_raw = cursor.fetchall()
        columns = []
        for c in columns_raw:
            columns.append(c[1])
    ### now execute the query    
    cursor.execute(query)
    output = cursor.fetchall()
    return columns, output

def execute_query_sqlalchemy(query):
    """
    Perform a query on the db
    """
    session.query(BenchmarkMeasurement).all()
    
def upload_test_result(timing_data,app_data):
    """
    Save data from a user-specified circuit test.
    """
    print("Uploading result to DB")
    cm = CustomMeasurement(
        circuit_path = app_data["uploaded_filenames"]["circuit_file"],
        context_name = app_data["HE_library"],
        input_type = app_data["input_type"],
        setup_time = timing_data[0],
        encryption_time = timing_data[1],
        evaluation_time = timing_data[2],
        decryption_time = timing_data[3])
    session.add(cm)
    session.commit()
        
def build_filter(input_dict):
    """
    convert dict of inputs from web form PlotsForm into SQLAlchemy filter.
    """
    field_to_attribute_dict = {
        "context_selections" : BenchmarkMeasurement.context_name,
        "gate_selections" : BenchmarkMeasurement.gate_name,
        "input_type_width" : BenchmarkMeasurement.input_bitwidth,
        "input_type_signed" : BenchmarkMeasurement.input_signed
    }
    and_expr = and_()
    for field, values in input_dict.items():
        if not field in field_to_attribute_dict.keys():
            continue
        or_expr = or_()
        for val in values:
            or_expr += field_to_attribute_dict[field] == val
        and_expr &= or_expr
    return and_expr
