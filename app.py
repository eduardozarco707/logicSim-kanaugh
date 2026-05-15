import re
import itertools
from flask import Flask, render_template, request, jsonify
from sympy import symbols, Or, And, Not
from sympy.logic import SOPform

# Aseguramos que Flask sepa dónde buscar los archivos estáticos
app = Flask(__name__, static_url_path='', static_folder='static')

@app.route('/')
def index():
    return render_template('index.html')

# NUEVA RUTA PARA EL SIMULADOR A PANTALLA COMPLETA
@app.route('/circuito')
def circuito():
    return render_template('circuito.html')

@app.route('/calcular', methods=['POST'])
def calcular():
    datos = request.get_json()
    n_entradas = int(datos.get('n_entradas', 3))
    filas_activas = datos.get('filas_activas', [])
    nombres_vars = datos.get('nombres_vars', [])
    
    if not filas_activas:
        return jsonify({'resultado': "0", 'explicaciones': []})
        
    sym_vars = [symbols(v) for v in nombres_vars]
    expr_sympy = SOPform(sym_vars, filas_activas)
    
    resultado_simplificado = ""
    explicaciones = []
    
    if expr_sympy == True or str(expr_sympy) == "True":
        resultado_simplificado = "1"
        explicaciones = [{'filas': [], 'eliminadas': nombres_vars, 'term_visual': '1', 'indices': filas_activas, 'term_data': []}]
    elif expr_sympy == False or str(expr_sympy) == "False":
        resultado_simplificado = "0"
    else:
        if expr_sympy.func == Or:
            agrupaciones = expr_sympy.args 
        else:
            agrupaciones = [expr_sympy]    

        for term in agrupaciones:
            if term.func == And:
                literales = term.args
            else:
                literales = [term]

            fixed_vars = {}
            for lit in literales:
                if lit.func == Not:
                    fixed_vars[str(lit.args[0])] = 0
                else:
                    fixed_vars[str(lit)] = 1

            eliminated = [v for v in nombres_vars if v not in fixed_vars]

            filas = []
            indices_decimales = []
            num_elim = len(eliminated)
            
            for combo in itertools.product([0, 1], repeat=num_elim):
                fila_dict = {}
                for k, v in fixed_vars.items():
                    fila_dict[k] = v
                for i, var_elim in enumerate(eliminated):
                    fila_dict[var_elim] = combo[i]
                
                fila_lista = [fila_dict[var] for var in nombres_vars]
                filas.append(fila_lista)
                
                dec_idx = 0
                for bit in fila_lista:
                    dec_idx = (dec_idx << 1) | bit
                indices_decimales.append(dec_idx)

            term_visual = ""
            term_data = []
            for var in nombres_vars:
                if var in fixed_vars:
                    term_visual += var if fixed_vars[var] == 1 else f'<span class="overline">{var}</span>'
                    term_data.append({'var': var, 'negated': fixed_vars[var] == 0})

            explicaciones.append({
                'filas': filas,
                'eliminadas': eliminated,
                'term_visual': term_visual,
                'indices': indices_decimales,
                'term_data': term_data
            })

        res_str = str(expr_sympy)
        res_str = re.sub(r'~(\w+)', r'<span class="overline">\1</span>', res_str)
        res_str = res_str.replace(' & ', '')
        res_str = res_str.replace(' | ', ' + ')
        res_str = res_str.replace('(', '').replace(')', '')
        resultado_simplificado = res_str
        
    return jsonify({
        'resultado': resultado_simplificado,
        'explicaciones': explicaciones
    })

if __name__ == '__main__':
    app.run(debug=True)