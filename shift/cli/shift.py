# -*- coding: utf-8 -*-
# Copyright (c) 2022, Alliance for Sustainable Energy, LLC

# All rights reserved.

# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:

# 1. Redistributions of source code must retain the above copyright notice, this
#    list of conditions and the following disclaimer.

# 2. Redistributions in binary form must reproduce the above copyright notice,
#    this list of conditions and the following disclaimer in the documentation
#    and/or other materials provided with the distribution.

# 3. Neither the name of the copyright holder nor the names of its
#    contributors may be used to endorse or promote products derived from
#    this software without specific prior written permission.

# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
# AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
# IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
# DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE
# FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL
# DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR
# SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER
# CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY,
# OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
# OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

"""This module handles command line interface for this package. """
import json

import click
import yaml

from shift.config_template import ConfigTemplate
from shift.facade import generate_feeder_from_yaml


@click.command()
@click.option("-c", "--config-yaml", help="Path to config yaml file.")
def create_config_file(config_yaml: str) -> None:
    """Creates a default config yaml file. Update this yaml file and use it to
    create the synthetic distribution feeder.
    """
    config = ConfigTemplate().dict()
    print(json.loads(json.dumps(config)))
    with open(config_yaml, "w", encoding="utf-8") as fpointer:
        yaml.dump(json.loads(json.dumps(config)), fpointer)


@click.command()
@click.option("-c", "--config-yaml", help="Path to config yaml file.")
def create_feeder(config_yaml: str) -> None:
    """Creates a synthetic distribution feeder
    by taking the config yaml file as an input.
    """
    generate_feeder_from_yaml(config_yaml)


@click.group()
def cli():
    """Entry point"""
    pass


cli.add_command(create_config_file)
cli.add_command(create_feeder)
