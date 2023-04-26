from base64 import b64decode
import base64
import glob
import gzip
import zlib

from Bio.SeqUtils import seq3
from Bio.Seq import Seq
from Bio.Data.CodonTable import TranslationError
from dash_bio.utils import protein_reader as pr

from dash import callback_context
from dash.dash import no_update
from dash.dependencies import Input, Output, State
from dash import dcc
from dash import html
import dash_bio


from server import run_standalone_app


# Preset colors for the shown molecules
COLORS = [
    '#e41a1c',
    '#377eb8',
    '#4daf4a',
    '#984ea3',
    '#ff7f00',
    '#ffff33',
    '#a65628',
    '#f781bf',
    '#999999',
]

# Possible molecular representations
REPRESENTATIONS = [
    'axes',
    'axes+box',
    'backbone',
    'ball+stick',
    'cartoon',
    'helixorient',
    'hyperball',
    'licorice',
    'line',
    'ribbon',
    'rope',
    'spacefill',
    'surface',
    'trace',
    'tube',
    'unitcell',
]

# PDB examples
PDBS = [
    '1ake',
    '1crn',
    'test',
]

# Placeholder which is loaded if no molecule is selected
data_dict = {
    'filename': 'placeholder',
    'ext': '',
    'selectedValue': 'placeholder',
    'chain': 'ALL',
    'aaRange': 'ALL',
    'chosenAtoms': '',
    'color': '#e41a1c',
    'config': {'type': '', 'input': ''},
    'uploaded': False,
    'resetView': False,
}

fasta_seq=''
# Canvas container to display the structures
component_id = 'nglViewer'
viewer = html.Div(
    id='ngl-biomolecule-viewer',
    children=[dash_bio.NglMoleculeViewer(
        id=component_id,
        data=[data_dict])],
)

def header_colors():
    return {'bg_color': '#e7625f', 'font_color': 'white'}


def description():
    return (
        'Molecule visualization in 3D - perfect for viewing '
        'biomolecules such as proteins, DNA and RNA. Includes '
        'stick, cartoon, and sphere representation.'
    )


placeholder = html.Div(id='ngl-placeholder', style={'textAlign': 'center', 'fontSize': '25px'})


data_tab = [
    html.Div(className='app-controls-name', children='Select structure',),
    dcc.Dropdown(
        id='pdb-dropdown',
        clearable=False,
        options=[{'label': k, 'value': k} for k in PDBS],
        # value='1ake',
        placeholder='placeholder',
    ),
    html.Div(
        children=[
            html.P(
                'Show multiple structures and (or) \
                specify a chain/ residues range/ \
                highlight chosen residues/ atoms',
                style={'fontSize': '10pt'},
            )
        ]
    ),
    dcc.Input(
        id='pdb-string',
        placeholder='pdbID1.chain:start-end@atom1,atom2_pdbID2.chain:start-end',
        value='1AKE.A:1-450@50,100,150_1AKE.A',
        style={'width': '100%'}),
    html.Br(),
    html.Button('Submit', id='btn-pdbString'),
    html.Button('Reset View', id='btn-resetView'),
    html.Br(),
    html.Div(
        title='Upload biomolecule to view here',
        className='app-controls-block',
        id='ngl-upload-container',
        children=[
            dcc.Upload(
                id='ngl-upload-data',
                className='control-upload',
                children=html.Div(
                    ['Drag and drop or click to upload (multiple) pdb/cif(.gz) file(s).']
                ),
                # Allow multiple files to be uploaded
                multiple=True,
            ),
            html.Div(id='warning_div', children=html.Div(['']))
        ],
    ),
]

fasta_tab =[
        html.Div(className='control-tab', children=[
            html.Div(className='app-controls-block', children=[
                        dcc.Input(
                            id='seqstring',
                            placeholder='Input Sequence',
                            value='Input Sequence',
                            style={'width': '100%'}),
                        html.Br(),
                        html.Button('Submit', id='seq-btnString'),
                        html.Br(),
                        html.Div(
                                    "Upload fasta format ",
                                    className='app-controls-name'
                                ),
                        html.Div(
                            id='seq-view-fasta-upload',
                            children=[
                                dcc.Upload(
                                    id='upload-fasta-data',
                                    className='control-upload',
                                    children=html.Div([
                                        "Drag and drop or click to upload a \
                                        file."
                                    ]),
                                ),
                            ]
                        ),
                    ])
            ])
]

view_tab = [
    html.Div(
        title="select molecule style",
        className="app-controls-block",
        id="ngl-mols-style",
        children=[
            html.P(
                "Style",
                style={"fontWeight": "bold", "marginBottom": "10px"},
            ),
            dcc.Dropdown(
                id="molecules-represetation-style",
                options=[{"label": e, "value": e.lower()} for e in REPRESENTATIONS],
                placeholder="select molecule style",
                value=['cartoon', 'axes+box'],
                multi=True
            ),
        ],
    ),
    # html.Div(
    #     title='set molecules x-axis spacing (if side by side is enabled)',
    #     className='app-controls-block',
    #     id='ngl-mols-spacing',
    #     children=[
    #         html.P(
    #             'x-axis spacing',
    #             style={'fontWeight': 'bold', 'marginBottom': '10px'},
    #         ),
    #         dcc.Input(
    #             id='molecules-xaxis-spacing',
    #             placeholder='set x-axis spacing',
    #             value=100,
    #         )
    #     ],
    # ),
    html.Div(
        title='set chain color',
        className='app-controls-block',
        id='ngl-mols-color',
        children=[
            html.P(
                'Chain colors',
                style={'fontWeight': 'bold',
                       'marginBottom': '10px'},
            ),
            dcc.Input(
                id='molecules-chain-color',
                value=','.join(COLORS),
            ),
        ],
    ),
    # html.Div(
    #     title='set chosen atoms color',
    #     className='app-controls-block',
    #     id='ngl-atom-color',
    #     children=[
    #         html.P(
    #             'Chosen atoms Color',
    #             style={'fontWeight': 'bold', 'marginBottom': '10px'},
    #         ),
    #         dcc.Input(
    #             id='chosen-atoms-color',
    #             value='#ffffff'
    #         ),
    #     ],
    # ),
    # html.Div(
    #     title='set chosen atoms radius',
    #     className='app-controls-block',
    #     id='ngl-atom-radius',
    #     children=[
    #         html.P(
    #             'Chosen atoms radius',
    #             style={'fontWeight': 'bold', 'marginBottom': '10px'},
    #         ),
    #         dcc.Input(
    #             id='chosen-atoms-radius',
    #             value='1.1'
    #         ),
    #     ],
    # ),
    html.Div(
        title='set background color',
        className='app-controls-block',
        id='ngl-style-color',
        children=[
            html.P(
                'Background color',
                style={'fontWeight': 'bold', 'marginBottom': '10px'},
            ),
            dcc.Dropdown(
                id='stage-bg-color',
                options=[
                    {'label': c, 'value': c.lower()}
                    for c in ['black', 'white']],
                value='white',
            ),
        ],
    ),
    html.Div(
        title='Camera settings',
        className='app-controls-block',
        id='ngl-selection-display',
        children=[
            html.P(
                'Camera settings',
                style={'fontWeight': 'bold', 'marginBottom': '10px'},
            ),
            dcc.Dropdown(
                id='stage-camera-type',
                options=[
                    {'label': k.capitalize(), 'value': k}
                    for k in ['perspective', 'orthographic']
                ],
                value='perspective',
            ),
        ],
    ),
    html.Div(
        title='select render quality',
        className='app-controls-block',
        id='ngl-style',
        children=[
            html.P(
                'Render quality',
                style={'fontWeight': 'bold', 'marginBottom': '10px'},
            ),
            dcc.Dropdown(
                id='stage-render-quality',
                options=[
                    {'label': c, 'value': c.lower()}
                    for c in ['auto', 'low', 'medium', 'high']
                ],
                value='auto',
            ),
        ],
    ),
]

tabs = html.Div(
    id='ngl-control-tabs',
    className='control-tabs',
    children=[
        dcc.Tabs(
            id='ngl-tabs',
            value='what-is',
            children=[
                dcc.Tab(
                    label='Data',
                    value='upload-select',
                    children=html.Div(className='control-tab', children=data_tab),
                ),
                dcc.Tab(
                    label="Fasta",
                    value="fasta-options",
                    children=[html.Div(className="control-tab", children=fasta_tab)],
                ),
                dcc.Tab(
                    label='View',
                    value='view-options',
                    children=[html.Div(className='control-tab', children=view_tab)],
                ),
            ],
        ),
    ],
)


def layout():
    return html.Div(
        id='main-page',
        children=[
            # keeps the data till the browser/tab closes.
            dcc.Store(
                id='uploaded-files',
                storage_type='session'
            ),
            html.Div(
                id='app-content',
                children=[
                    html.Div(
                        id='ngl-body',
                        className='app-body',
                        children=[
                            tabs,
                            placeholder,
                            viewer,
                        ],
                    ),
                ],
            ),
        ],
    )


def create_dict(
        filename,
        ext,
        selection,
        chain,
        aa_range,
        highlight_dic,
        color,
        content,
        resetView=False,
        uploaded=False
):
    return {
        'filename': filename,
        'ext': ext,
        'selectedValue': selection,
        'chain': chain,
        'aaRange': aa_range,
        'chosen': highlight_dic,
        'color': color,
        'config': {'type': 'text/plain', 'input': content},
        'resetView': resetView,
        'uploaded': uploaded
    }


def get_highlights(string, sep, atom_indicator):

    residues_list = []
    atoms_list = []

    str_, _str = string.split(sep)
    for e in _str.split(','):
        if atom_indicator in e:
            atoms_list.append(e.replace(atom_indicator, ''))
        else:
            residues_list.append(e)

    return (
        str_, {
            'atoms': ','.join(atoms_list),
            'residues': ','.join(residues_list),
        })


# Helper function to load structures from local storage
def getLocalData(selection, pdb_id, color, uploadedFiles, resetView=False):

    chain = 'ALL'
    aa_range = 'ALL'
    highlight_dic = {
        'atoms': '',
        'residues': ''
    }

    # Check if only one chain should be shown
    if '.' in pdb_id:
        pdb_id, chain = pdb_id.split('.')

        highlights_sep = '@'
        atom_indicator = 'a'
        # Check if only a specified amino acids range should be shown:
        if ':' in chain:
            chain, aa_range = chain.split(':')

            # Check if atoms should be highlighted
            if highlights_sep in aa_range:
                aa_range, highlight_dic = get_highlights(
                    aa_range, highlights_sep, atom_indicator)

        else:
            if highlights_sep in chain:
                chain, highlight_dic = get_highlights(
                    chain, highlights_sep, atom_indicator)

    if pdb_id not in PDBS:
        if pdb_id in uploadedFiles:
            fname = [i for i in uploadedFiles[:-1].split(',') if pdb_id in i][0]

            content = ''
            return create_dict(
                fname,
                fname.split('.')[1],
                selection,
                chain,
                aa_range,
                highlight_dic,
                color,
                content,
                resetView,
                uploaded=False,
            )
        return data_dict

    # get path to protein structure
    fname = [f for f in glob.glob('pdb/' + pdb_id + '.*')][0]

    if "gz" in fname:
        ext = fname.split('.')[-2]
        with gzip.open(fname, 'r') as fh:
            content = fh.read().decode('UTF-8')
    else:
        ext = fname.split('.')[-1]
        with open(fname, 'r') as fh:
            content = fh.read()

    filename = fname.split('/')[-1]

    return create_dict(
        filename,
        ext,
        selection,
        chain,
        aa_range,
        highlight_dic,
        color, content,
        resetView,
        uploaded=False
    )

def update_sequence(upload_contents):

        if upload_contents is not None:
            data = ''
            try:
                content_string = upload_contents.split(',')
                data = base64.b64decode(content_string).decode('UTF-8')
            except AttributeError:
                pass
            if data == '':
                return '-'

            protein = pr.read_fasta(data, is_datafile=False)
        else:
            return '-'
        print(protein)
        return protein['sequence']

def model(seq):
    return "abc"

def getPdb_from_model(sequence):
    data = []
    uploads = []

    ext = 'pdb'
    chain = 'ALL'
    aa_range = 'ALL'
    highlight_dic = {
        'atoms': '',
        'residues': ''
        }
    
    pdb_file = model(sequence)

    for i, content in enumerate(pdb_file):
        content = str(content).split(',')

        content = content.decode('UTF-8')

        pdb_id = content.split('\n')[0].split()[-1]
        if 'data_' in pdb_id:
            pdb_id = pdb_id.split('_')[1]
            ext = 'cif'

        filename = pdb_id + '.' + ext
        uploads.append(filename)

        data.append(
            create_dict(
                filename,
                ext,
                pdb_id,
                chain,
                aa_range,
                highlight_dic,
                COLORS[i],
                content,
                resetView=False,
                uploaded=True,
            )
        )
    return data, uploads
    



# Helper function to load structures from uploaded content
def getUploadedData(uploaded_content):
    data = []
    uploads = []

    ext = 'pdb'
    chain = 'ALL'
    aa_range = 'ALL'
    highlight_dic = {
        'atoms': '',
        'residues': ''
        }

    for i, content in enumerate(uploaded_content):
        content_type, content = str(content).split(',')

        if "gzip" in content_type:
            content = zlib.decompress(
                b64decode(content),
                zlib.MAX_WBITS | 16
            )
        else:
            content = b64decode(content)

        content = content.decode('UTF-8')

        pdb_id = content.split('\n')[0].split()[-1]
        if 'data_' in pdb_id:
            pdb_id = pdb_id.split('_')[1]
            ext = 'cif'

        filename = pdb_id + '.' + ext
        uploads.append(filename)

        data.append(
            create_dict(
                filename,
                ext,
                pdb_id,
                chain,
                aa_range,
                highlight_dic,
                COLORS[i],
                content,
                resetView=False,
                uploaded=True,
            )
        )

    return data, uploads


def callbacks(_app):

    # Callback for molecule visualization based on the dropdown selection
    @_app.callback(
        [
            Output(component_id, 'data'),
            Output(component_id, "molStyles"),
            Output('pdb-dropdown', 'options'),
            Output('uploaded-files', 'data'),
            Output('pdb-dropdown', 'placeholder'),
            Output('warning_div', 'children'),
        ],
        [
            Input('pdb-dropdown', 'value'),
            Input('ngl-upload-data', 'contents'),
            Input('btn-pdbString', 'n_clicks'),
            Input('btn-resetView', 'n_clicks'),

            Input('molecules-represetation-style', 'value'),

            Input('seqstring', 'value'),
            Input('seq-btnString', 'n_clicks'),
            Input('upload-fasta-data', 'contents')
        ],
        [
            State('pdb-string', 'value'),
            State('pdb-dropdown', 'options'),
            State('uploaded-files', 'data'),
            State('molecules-chain-color', 'value'),
            # State('chosen-atoms-color', 'value'),
            # State('chosen-atoms-radius', 'value'),
            # State('molecules-xaxis-spacing', 'value'),
        ]
    )
    def display_output(
            selection,
            uploaded_content,
            pdbString_clicks,
            resetView_clicks,

            molStyles_list,

            seqstring,
            seqString_clicks,
            fasta_content,

            pdbString,
            dropdown_options,
            files,
            colors,
            # chosenAtomsColor,
            # chosenAtomsRadius,
            # molSpacing_xAxis,
            # sideByside_text
    ):  
        seqstring= ''
        input_id = None
        options = dropdown_options
        colors_list = colors.split(',')

        # Give a default data dict if no files are uploaded
        files = files or {'uploaded': []}

        molstyles_dict = {
            'representations': molStyles_list,
            'chosenAtomsColor': '#ffffff',
            'chosenAtomsRadius': 1.1,
            'molSpacingXaxis': 100,
        }

        ctx = callback_context
        if ctx.triggered:
            input_id = ctx.triggered[0]['prop_id'].split('.')[0]

        if input_id is None:
            return [data_dict], molstyles_dict, options, files, no_update, no_update

        if input_id == 'pdb-dropdown':
            pdb_id = selection

            if pdb_id in files:
                fname = [i for i in files[:-1].split(',') if pdb_id in i][0]

                content = ''
                chain = 'ALL'
                aa_range = 'ALL'
                highlight_dic = {
                    'atoms': '',
                    'residues': ''
                }
                return (
                    [create_dict(
                        fname,
                        fname.split('.')[1],
                        pdb_id,
                        chain,
                        aa_range,
                        highlight_dic,
                        colors_list[0],
                        content,
                        resetView=False,
                        uploaded=False,
                    )],
                    molstyles_dict,
                    options,
                    files,
                    no_update,
                    no_update
                )

            return ([getLocalData(selection,
                                  pdb_id,
                                  colors_list[0],
                                  files,
                                  resetView=False)],
                    molstyles_dict,
                    options,
                    files,
                    no_update,
                    no_update
                    )

        # TODO submit and reset view in one button

        if input_id == "seqstring":
            return no_update, no_update, no_update, no_update, no_update, no_update
        
        if input_id == "upload-fasta-data":
            seqstring = update_sequence(fasta_content)
            data, uploads = getPdb_from_model(seqstring)

            for pdb_id, ext in [e.split('.') for e in uploads]:
                if pdb_id not in [e['label'] for e in options]:
                    options.append({'label': pdb_id, 'value': pdb_id})
                    fname = pdb_id + "." + ext

                    if fname not in files["uploaded"]:
                        files["uploaded"].append(fname)

            return data, molstyles_dict, options, files, pdb_id, no_update


        if input_id == "molecules-represetation-style":
            return no_update, molstyles_dict, no_update, no_update, no_update, no_update
        
        if input_id in ['seq-btnString']:
            if seqstring is not None:
                data, uploads = getPdb_from_model(seqstring)

            for pdb_id, ext in [e.split('.') for e in uploads]:
                if pdb_id not in [e['label'] for e in options]:
                    options.append({'label': pdb_id, 'value': pdb_id})
                    fname = pdb_id + "." + ext

                    if fname not in files["uploaded"]:
                        files["uploaded"].append(fname)

            return data, molstyles_dict, options, files, pdb_id, no_update
        
        if input_id in ['btn-pdbString', 'btn-resetView']:
            warning = ''

            if pdbString is None:
                return no_update, no_update, no_update, no_update, no_update, no_update

            reset_view = False
            if input_id == 'btn-resetView':
                reset_view = True

            data = []
            if len(pdbString) > 3:
                pdb_id = pdbString
                if '_' in pdbString:
                    for i, pdb_id in enumerate(pdbString.split('_')):
                        if i <= len(colors_list)-1:
                            data.append(
                                getLocalData(
                                    pdbString,
                                    pdb_id,
                                    colors_list[i],
                                    files,
                                    resetView=reset_view,
                                )
                            )
                        else:
                            data.append(data_dict)
                            warning = (
                                'more molecules selected as chain colors defined either \
                                  remove one molecule or add an extra color in the view tab \
                                  and reset view before submitting it again.')
                            return data, no_update, options, files, no_update, warning
                else:
                    data.append(
                        getLocalData(
                            pdbString,
                            pdb_id,
                            colors_list[0],
                            files,
                            resetView=reset_view,
                        )
                    )
            else:
                data.append(data_dict)

            return data, molstyles_dict, options, files, 'Select a molecule', warning

        if input_id == 'ngl-upload-data':
            data, uploads = getUploadedData(uploaded_content)

            for pdb_id, ext in [e.split('.') for e in uploads]:
                if pdb_id not in [e['label'] for e in options]:
                    options.append({'label': pdb_id, 'value': pdb_id})
                    fname = pdb_id + "." + ext

                    if fname not in files["uploaded"]:
                        files["uploaded"].append(fname)

            return data, molstyles_dict, options, files, pdb_id, no_update

        # if input_id == "molecules-represetation-style":
        #     return no_update, molstyles_dict, no_update, no_update, no_update, no_update

    # Callback for updating bg-color, camera-type and render quality
    @_app.callback(
        Output(component_id, 'stageParameters'),
        [
            Input('stage-bg-color', 'value'),
            Input('stage-camera-type', 'value'),
            Input('stage-render-quality', 'value'),
        ],
    )
    def update_stage(bgcolor, camera_type, quality):
        return {
            'backgroundColor': bgcolor,
            'cameraType': camera_type,
            'quality': quality,
        }

    # Callback for displaying placeholder for a blank stage.
    @_app.callback(
        Output('ngl-placeholder', 'children'),
        [
            Input(component_id, 'data'),
        ],
    )
    def update_viewer(data):
        if data[0]['filename'] == "placeholder":
            return " "



app = run_standalone_app(layout, callbacks, header_colors, __file__)
server = app.server

if __name__ == '__main__':
    app.run_server(debug=True, port=8050)