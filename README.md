## Setup
1. Install anaconda/miniconda: https://docs.conda.io/en/latest/miniconda.html
2. Create virtual enverioment: `conda create -n genescrape python=3`
3. Install librarias: `conda install -f requirements.txt`

## Usage
Help: `python main.py --help`

    usage: main.py [-h] [-i INPUT] [-o OUTPUT] [--log_json]
    
    optional arguments:
      -h, --help            show this help message and exit
      -i INPUT, --input INPUT
                            input file path
      -o OUTPUT, --output OUTPUT
                            output file path
      --log_json            Log received json data in same directory as output under a jsons directory

Example: `python main.py -i data/input_example.csv -o data/output_example.xlsx`