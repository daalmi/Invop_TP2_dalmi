import sys
#importamos el modulo cplex
import cplex

TOLERANCE =10e-6 

class InstanciaRecorridoMixto:
    def __init__(self):
        self.cant_clientes = 0
        self.costo_repartidor = 0
        self.d_max = 0
        self.refrigerados = []
        self.exclusivos = []
        self.distancias = []        
        self.costos = []        

    def leer_datos(self,filename):
        # abrimos el archivo de datos
        f = open(filename)

        # leemos la cantidad de clientes
        self.cantidad_clientes = int(f.readline())
        # leemos el costo por pedido del repartidor
        self.costo_repartidor = int(f.readline())
        # leemos la distamcia maxima del repartidor
        self.d_max = int(f.readline())
        
        # inicializamos distancias y costos con un valor muy grande (por si falta algun par en los datos)
        self.distancias = [[1000000 for _ in range(self.cantidad_clientes)] for _ in range(self.cantidad_clientes)]
        self.costos = [[1000000 for _ in range(self.cantidad_clientes)] for _ in range(self.cantidad_clientes)]
        
        # leemos la cantidad de refrigerados
        cantidad_refrigerados = int(f.readline())
        # leemos los clientes refrigerados
        for i in range(cantidad_refrigerados):
            self.refrigerados.append(int(f.readline()))
        
        # leemos la cantidad de exclusivos
        cantidad_exclusivos = int(f.readline())
        # leemos los clientes exclusivos
        for i in range(cantidad_exclusivos):
            self.exclusivos.append(int(f.readline()))
        
        # leemos las distancias y costos entre clientes
        lineas = f.readlines()
        for linea in lineas:
            row = list(map(int,linea.split(' ')))
            self.distancias[row[0]-1][row[1]-1] = row[2]
            self.distancias[row[1]-1][row[0]-1] = row[2]
            self.costos[row[0]-1][row[1]-1] = row[3]
            self.costos[row[1]-1][row[0]-1] = row[3]
        
        # cerramos el archivo
        f.close()

def cargar_instancia():
    # El 1er parametro es el nombre del archivo de entrada
    nombre_archivo = sys.argv[1].strip()
    # Crea la instancia vacia
    instancia = InstanciaRecorridoMixto()
    # Llena la instancia con los datos del archivo de entrada 
    instancia.leer_datos(nombre_archivo)
    return instancia

def agregar_variables(prob, instancia):
    # Definir y agregar las variables:
	# metodo 'add' de 'variables', con parametros:
	# obj: costos de la funcion objetivo
	# lb: cotas inferiores
    # ub: cotas superiores
    # types: tipo de las variables
    # names: nombre (como van a aparecer en el archivo .lp)
    n = instancia.cantidad_clientes
    
    # Poner nombre a las variables y llenar coef_funcion_objetivo
    nombres = [f"x_{i}{0}" for i in range(1,n+1)] + [f"x_{0}{j}" for j in range(1,n+1)] + [f"x_{i}{j}" for i in range(1,n+1) for j in range(1,n+1)] + [f"y_{i}{j}" for i in range(1,n+1) for j in range(1,n+1)] + [f"c_{i}" for i in range(1,n+1)] + [f"b_{i}" for i in range(1,n+1)] + [f"D_{i}" for i in range(1,n+1)] + [f"u_{i}" for i in range(1,n+1)]
    coeficientes_funcion_objetivo = [0 for _ in range(0,2*n)] + [instancia.costos[i][j] for i in range(0,n) for j in range(0,n)] + [0 for _ in range(1,n+1) for _ in range(1,n+1)] + [0 for _ in range(1,n+1)] + [instancia.costo_repartidor for _ in range(1,n+1)] + [0 for _ in range(1,n+1)] + [0 for _ in range(1,n+1)] 
    prob.variables.add(obj = coeficientes_funcion_objetivo, lb = [0 for _ in nombres], ub = [1 for _ in nombres[:-n]] + [n-1 for _ in range(n)], types = ["I" for _ in nombres], names = nombres)

def agregar_restricciones(prob, instancia):
    # Agregar las restricciones ax <= (>= ==) b:
	# funcion 'add' de 'linear_constraints' con parametros:
	# lin_expr: lista de listas de [ind,val] de a
    # sense: lista de 'L', 'G' o 'E'
    # rhs: lista de los b
    # names: nombre (como van a aparecer en el archivo .lp)

    # Notar que cplex espera "una matriz de restricciones", es decir, una
    # lista de restricciones del tipo ax <= b, [ax <= b]. Por lo tanto, aun cuando
    # agreguemos una unica restriccion, tenemos que hacerlo como una lista de un unico
    # elemento.
    n = instancia.cantidad_clientes
    nombres = prob.variables.get_names()
    
    a1 = [[[i for i in range(0,n)], [1]*n]]
    b1 = [1 for _ in range(len(a1))]
    s1 = ['E' for _ in range(len(a1))]
    n1 = ['entro_0']
    prob.linear_constraints.add(lin_expr = a1, sense = s1, rhs = b1, names = n1)
    
    a2 = [[[i+n for i in range(0,n)], [1]*n]]
    b2 = [1 for _ in range(len(a2))]
    s2 = ['E' for _ in range(len(a2))]
    n2 = ['salgo_0']
    prob.linear_constraints.add(lin_expr = a2, sense = s2, rhs = b2, names = n2)
    
    a3 = [[[i]+[j+n*i+2*n for j in range(0,n)]+[i+2*n**2+2*n], [1]*(n+1)+[-1]] for i in range(0,n)]  #3, otra manera: [[[j for j in range(len(nombres)) if nombres[j][0:3] == f"x_{i}"]+[i+2*n**2-1], [1]*n+[-1]] for i in range(1,n+1)]
    b3 = [0 for _ in range(len(a3))]
    s3 = ['E' for _ in range(len(a3))]
    n3 = [f'salgo_camion_{i}' for i in range(len(a3))]
    prob.linear_constraints.add(lin_expr = a3, sense = s3, rhs = b3, names = n3)

    a4 = [[[n+j]+[j+n*i+2*n for i in range(0,n)]+[j+2*n**2+2*n], [1]*(n+1)+[-1]] for j in range(0,n)]  #4, otra manera:  [[[i for i in range(len(nombres)) if nombres[i][0:2] == f"x_" and nombres[i][-1] == f"{j}"]+[j+2*n**2-1], [1]*n+[-1]] for j in range(1,n+1)]
    b4 = [0 for _ in range(len(a4))]
    s4 = ['E' for _ in range(len(a4))]
    n4 = [f'entro_camion_{i}' for i in range(len(a4))]
    prob.linear_constraints.add(lin_expr = a4, sense = s4, rhs = b4, names = n4)
    
    a5 = [[[i+2*n**2+2*n-1], [1]] for i in instancia.exclusivos] #5
    b5 = [1 for _ in range(len(a5))]
    s5 = ['E' for _ in range(len(a5))]
    n5 = [f'prioridad_{i}' for i in range(len(a5))]
    prob.linear_constraints.add(lin_expr = a5, sense = s5, rhs = b5, names = n5)
    
    a6 = [[[k+n**2+2*n,k//n+2*n**2+2*n], [1,-1]] for k in range(0,n**2)] #6, otra manera: [[[k for k in range(len(nombres)) if nombres[k][0:4] == f"y_{i}{j}"], [1]] for i in range(1,n+1) for j in range(1,n+1)] 
    b6 = [1 for _ in range(len(a6))]
    s6 = ['L' for _ in range(len(a6))]
    n6 = [f'pasa_bici_paso_bondi{i}' for i in range(len(a6))]
    prob.linear_constraints.add(lin_expr = a6, sense = s6, rhs = b6, names = n6)
    
    a7 = [[[i+2*n**2+2*n,i+3*n+2*n**2], [1,1]] for i in range(0,n)] #7
    b7 = [1 for _ in range(len(a7))]
    s7 = ['E' for _ in range(len(a7))]
    n7 = [f'camion_bici_{i}' for i in range(len(a7))]
    prob.linear_constraints.add(lin_expr = a7, sense = s7, rhs = b7, names = n7)
    
    a8 = [[[i*n+n**2+2*n+j for i in range(0,n)]+[2*n**2+3*n+j], [1]*n+[-1]] for j in range(0,n)] #8, otra manera: [[[i for i in range(len(nombres)) if nombres[i][0:2] == f"y_" and nombres[i][-1] == f"{j}"]+[2*n**2+n+j-1], [1]*n+[-1]] for j in range(1,n+1)] 
    b8 = [0 for _ in range(len(a8))]
    s8 = ['E' for _ in range(len(a8))]
    n8 = [f'llego_bici_salio_bici{i}' for i in range(len(a8))]
    prob.linear_constraints.add(lin_expr = a8, sense = s8, rhs = b8, names = n8)
    
    a9 = [[[k for k in range(len(nombres)) if nombres[k][0:4] == f"y_{i}{j}"], [instancia.distancias[i][j]]] for i in range(1,n+1) for j in range(1,n+1)] #9, otra manera: [[[k], [1]] for k in range(n**2,2*n**2)] y paso dividiendo dij
    b9 = [instancia.d_max for _ in range(len(a9))]
    s9 = ['L' for _ in range(len(a9))]
    n9 = [f'respeto_dmax-{i}' for i in range(len(a9))]
    prob.linear_constraints.add(lin_expr = a9, sense = s9, rhs = b9, names = n9)
    
    a10 = [[[k+2*n, k//n+2*n**2+3*n], [1,-1]] for k in range(n**2,2*n**2)] #10, otra manera: [[[k for k in range(len(nombres)) if nombres[k][0:4] == f"y_{i}{j}"], [1]] for i in range(1,n+1) for j in range(1,n+1)]
    b10 = [0 for _ in range(len(a10))]
    s10 = ['L' for _ in range(len(a10))]
    n10 = [f'salgo_bici_{i}' for i in range(len(a10))]
    prob.linear_constraints.add(lin_expr = a10, sense = s10, rhs = b10, names = n10)
    
    a11 = [[[i*n+n**2+2*n+j for j in range(0,n)]+[2*n**2+4*n+i], [1]*n+[-4]] for i in range(0,n)] #11, otra manera: [[[j for j in range(len(nombres)) if nombres[j][0:3] == f"y_{i}"], [1]*n] for i in range(1,n+1)] 
    b11 = [0 for _ in range(len(a11))]
    s11 = ['G' for _ in range(len(a11))]
    n11 = [f'uso_bici_4_veces{i}' for i in range(len(a11))]
    prob.linear_constraints.add(lin_expr = a11, sense = s11, rhs = b11, names = n11)
    
    a12 = [[[i+3*n+2*n**2,i+5*n+2*n**2], [1,1]] for i in range(0,n)] #12a 
    b12 = [1 for _ in range(len(a12))]
    s12 = ['G' for _ in range(len(a12))]
    n12 = [f'continuidad_1_{i}' for i in range(len(a12))]
    prob.linear_constraints.add(lin_expr = a12, sense = s12, rhs = b12, names = n12)
    
    a13 = [[[k+3*n+2*n**2 for k in range(0,n)]+[i+5*n+2*n**2], [1]*(n+1)] for i in range(0,n)] #12b
    b13 = [n-1 for _ in range(len(a13))]
    s13 = ['L' for _ in range(len(a13))]
    n13 = [f'continuidad_2_{i}' for i in range(len(a13))]
    prob.linear_constraints.add(lin_expr = a13, sense = s13, rhs = b13, names = n13)
    
    a14 = [[[i+5*n+2*n**2]+[j+5*n+2*n**2]+[2*n+i*n+j], [1,-1,n-1]] for i in range(0,n) for j in range(0,n)]
    b14 = [n-1 for _ in range(len(a14))]
    s14 = ['L' for _ in range(len(a14))]
    n14 = [f'continuidad_3_{i}' for i in range(len(a14))]
    prob.linear_constraints.add(lin_expr = a14, sense = s14, rhs = b14, names = n14)
    
    
def armar_lp(prob, instancia):

    # Agregar las variables
    agregar_variables(prob, instancia)
   
    # Agregar las restricciones 
    agregar_restricciones(prob, instancia)

    # Setear el sentido del problema
    prob.objective.set_sense(prob.objective.sense.minimize)

    # Escribir el lp a archivo
    prob.write('recorridoMixto.lp')

def resolver_lp(prob):
    
    # Definir los parametros del solver
    prob.parameters.mip.strategy.heuristicfreq.set(1)
    prob.parameters.preprocessing.presolve.set(1)
    prob.parameters.mip.strategy.branch.set(-1)
       
    # Resolver el lp
    prob.solve()

def mostrar_solucion(prob,instancia):
    
    # Obtener informacion de la solucion a traves de 'solution'
    
    # Tomar el estado de la resolucion
    status = prob.solution.get_status_string(status_code = prob.solution.get_status())
    
    # Tomar el valor del funcional
    valor_obj = prob.solution.get_objective_value()
    
    print('Funcion objetivo: ',valor_obj,'(' + str(status) + ')')
    
    # Tomar los valores de las variables
    x  = prob.solution.get_values()

    # Mostrar las variables con valor positivo (mayor que una tolerancia)
    for i in range(len(x)):
        if x[i] > TOLERANCE:
            print(prob.variables.get_names()[i] + ":", x[i])

def main():
    
    # Lectura de datos desde el archivo de entrada
    instancia = cargar_instancia()
    
    # Definicion del problema de Cplex
    prob = cplex.Cplex()
    
    # Definicion del modelo
    armar_lp(prob,instancia)

    # Resolucion del modelo
    resolver_lp(prob)

    # Obtencion de la solucion
    mostrar_solucion(prob,instancia)

if __name__ == '__main__':
    main()