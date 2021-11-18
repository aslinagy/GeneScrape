import json
import time
import requests
import argparse
import pandas as pd

from tqdm import tqdm
from pathlib import Path
from collections import defaultdict


def parse_args():
    parser = argparse.ArgumentParser()

    parser.add_argument('-i', '--input', type=str, help='input file path')
    parser.add_argument('-o', '--output', type=str, help='output file path')
    parser.add_argument('--log_json', action='store_true',
                        help='Log received json data in same directory as output under a jsons directory')

    return parser.parse_args()


def make_request(uri, headers={'Accept': 'application/json'}):
    r = requests.get(uri, headers=headers)

    if r.ok:
        data = r.json()
    else:
        data = defaultdict(str)
        data['name'] = str(r.status_code)
    return data


def make_genename_request(symbol_id):
    uri = f'http://rest.genenames.org/fetch/symbol/{symbol_id}'

    return make_request(uri)


def make_uniprot_request(uniprot_ids):
    uri = "https://www.ebi.ac.uk/proteins/api/proteins/{}"

    res = [make_request(uri.format(_id)) for _id in uniprot_ids]

    return res


def parse_data(gene_data, uniprot_data):
    def get_uniprot_name(data):
        ret = ''
        try:
            ret = data['protein']['recommendedName']['fullName']['value']
        except KeyError:
            pass

        return ret

    def get_uniprot_function(data):
        function_sec = [c for c in data['comments'] if c['type'] == 'FUNCTION']
        values = []
        for sec in function_sec:
            for sub_sec in sec['text']:
                values.append(sub_sec['value'])

        return '\n\n'.join(values)

    def get_uniprot_subcell_loc(data):
        sl = [c for c in data['comments'] if c['type'] == 'SUBCELLULAR_LOCATION']
        sub_locations = [x['location']['value'] for ssl in sl if 'locations' in ssl for x in ssl['locations']]
        extra_notes = [y['value'] for x in sl if 'text' in x for y in x['text']]

        return '\n'.join(sub_locations+extra_notes)

    def get_uniprot_disease_biotech(data):
        def parse_disease(sec):

            disease_id = sec['diseaseId'] if 'diseaseId' in sec else ''
            acronym = f"({sec['acronym']})" if 'acronym' in sec else ''

            text = '\n'.join(x['value'] for x in sec['text']) if 'text' in sec else ''
            desc = sec['description']['value'] if 'description' in sec else ''

            res = f'{disease_id} {acronym}\n{text}\n{desc}'.strip()

            return res

        biotech_sections = [c for c in data['comments'] if c['type'] == 'BIOTECHNOLOGY']
        patholgy_sections = [c for c in data['comments'] if c['type'] == 'DISEASE']

        res = ''
        if patholgy_sections:
            res += 'Involvement in disease:\n'
            res += '\n\n'.join(parse_disease(sec) for sec in patholgy_sections)
            res.strip()

        if biotech_sections:
            if patholgy_sections:
                res += '\n\n'
            res += 'Biotechnological use:'
            res += '\n'.join([x['value'] for sec in biotech_sections for x in sec['text']])
            res.strip()

        return res

    def get_uniprot_dev_stage(data):
        dev = [c for c in data['comments'] if c['type'] == 'DEVELOPMENTAL_STAGE']
        values = [x['value'] for sec in dev for x in sec['text']]

        return '\n'.join(values)

    genenames_base_url = 'https://www.genenames.org/data/gene-symbol-report/#!/hgnc_id/{}'
    uniprot_base_url = 'https://www.uniprot.org/uniprot/{}'
    ensembl_base_url = 'http://www.ensembl.org/id/{}'
    genecard_base_url = 'https://www.genecards.org/cgi-bin/carddisp.pl?id_type=hgnc&id={}'
    quickgo_base_url = 'https://www.ebi.ac.uk/QuickGO/GProtein?ac={}'

    gene_data_dd = defaultdict(str)
    gene_data_dd.update(gene_data)
    rows = []

    for uniprot_row in uniprot_data:
        row = [
            ('Approved symbol:', gene_data_dd['symbol']),                                         # 1
            ('Approved name:', gene_data_dd['name']),                                             # 2
            ('Locus type:', gene_data_dd['locus_type']),                                          # 3
            ('Protein name: ',  get_uniprot_name(uniprot_row)),                                   # 4
            ('Genenames link:', genenames_base_url.format(gene_data_dd['hgnc_id'])),              # 5
            ('HGNC ID:', gene_data_dd['hgnc_id']),                                                # 6
            ('Ensembl ID:', gene_data_dd['ensembl_gene_id']),                                     # 7
            ('Ensembl link:', ensembl_base_url.format(gene_data_dd['ensembl_gene_id'])),          # 8
            ('UniProt ID:', gene_data_dd['uniprot_ids']),                                         # 9
            ('UniProt link:', uniprot_base_url.format(gene_data_dd['uniprot_ids'])),              # 10
            ('Genecards link:', genecard_base_url.format(gene_data_dd['hgnc_id'])),               # 11
            ('QuickGO link:', quickgo_base_url.format(gene_data_dd['uniprot_ids'])),              # 12
            ('Function:',  get_uniprot_function(uniprot_row)),                                    # 13
            ('Subcellular localization:', get_uniprot_subcell_loc(uniprot_row)),                  # 14
            ('Pathology and Biotech', get_uniprot_disease_biotech(uniprot_row)),                  # 15
            ('Expression/developmental stage:', get_uniprot_dev_stage(uniprot_row))               # 16
        ]
        rows.append(row)

    return rows


def make_output_df(rows):
    head_row = ['Field_ID_1', 'Field_ID_2', 'Field_ID_3', 'Field_ID_4', 'Field_ID_5', 'Field_ID_6', 'Field_ID_7',
                'Field_ID_8', 'Field_ID_9', 'Field_ID_10', 'Field_ID_11', 'Field_ID_12', 'Field_ID_13',
                'Field_ID_14', 'Field_ID_15', 'Field_ID_16']

    df_rows = []

    for i in range(len(head_row)):
        df_row = [head_row[i], rows[0][i][0]]
        for r in rows:
            df_row.append(r[i][1])

        df_rows.append(df_row)

    df = pd.DataFrame(df_rows)
    return df


if __name__ == '__main__':
    args = parse_args()
    in_df = pd.read_csv(args.input)

    # in_df = pd.read_csv('/home/joe/workspace/SzBK/GeneScrape/data/reportgenerator_example_input_MV_20211029.csv')

    rows = []
    no_response = []

    for gene_symbol in tqdm(in_df['Gene_name']):
        data_gene = make_genename_request(gene_symbol)

        if data_gene['response']['docs']:
            for i, resp in enumerate(data_gene['response']['docs']):
                uniprot_ids = resp['uniprot_ids']
                uniprot_data = make_uniprot_request(uniprot_ids)

                if args.log_json:
                    log_json_path = Path(args.output).parent / 'jsons'
                    log_json_path.mkdir(parents=True)
                    with open(f'{str(log_json_path)}/{gene_symbol}_genename_{i}.json', 'w') as f:
                        json.dump(resp, f, indent=4)

                    for j, uni_doc in enumerate(uniprot_data):
                        with open(f'{str(log_json_path)}/{gene_symbol}_uniprot_{j}.json', 'w') as f:
                            json.dump(uni_doc, f, indent=4)

                rows.extend(parse_data(resp, uniprot_data))
        else:
            no_response.append(gene_symbol)

        time.sleep(0.1)

    df = make_output_df(rows)
    if args.output.endswith('.csv'):
        df.to_csv(args.output, index=False)
    else:
        df.to_excel(args.output, index=False)

    if no_response:
        error_fn = str(Path(args.output).parent / f"{'.'.join(args.input.split('.')[:-1])}_invalid_gene_names.txt")
        with open(error_fn, 'w') as f:
            f.write('\n'.join(no_response))