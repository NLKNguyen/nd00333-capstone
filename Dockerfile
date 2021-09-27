FROM mcr.microsoft.com/azureml/openmpi3.1.2-ubuntu18.04

RUN conda install -y python=3.8
RUN conda install -y cython
RUN conda install -y numpy
RUN conda install -y pandas

RUN conda install -y -c conda-forge kats
RUN conda install -y -c conda-forge typer

RUN pip install azureml-defaults
