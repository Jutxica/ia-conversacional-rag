import json
import psycopg2
from psycopg2.extras import RealDictCursor, execute_values
from src.db import get_db_connection

class NeonResponse:
    def __init__(self, data=None, count=None):
        self.data = data if data is not None else []
        self.count = count

class NeonQueryBuilder:
    def __init__(self, table):
        self.table = table
        self.action = None
        self.columns = "*"
        self.count_exact = False
        self._eq = []
        self._in = []
        self._limit = None
        self._data = None

    def select(self, columns="*", count=None):
        self.action = "select"
        self.columns = columns
        if count == "exact":
            self.count_exact = True
        return self

    def insert(self, data):
        self.action = "insert"
        self._data = data if isinstance(data, list) else [data]
        return self

    def delete(self):
        self.action = "delete"
        return self

    def eq(self, column, value):
        self._eq.append((column, value))
        return self

    def in_(self, column, values):
        self._in.append((column, values))
        return self

    def limit(self, limit):
        self._limit = limit
        return self

    def execute(self):
        with get_db_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                where_clauses = []
                params = []

                for col, val in self._eq:
                    where_clauses.append(f"{col} = %s")
                    params.append(val)
                
                for col, vals in self._in:
                    if not vals:
                        where_clauses.append("1 = 0") # IN vazio
                    else:
                        where_clauses.append(f"{col} = ANY(%s)")
                        params.append(vals)

                where_str = ""
                if where_clauses:
                    where_str = " WHERE " + " AND ".join(where_clauses)

                limit_str = ""
                if self._limit is not None:
                    limit_str = f" LIMIT {self._limit}"

                if self.action == "select":
                    if self.count_exact and self.columns == "id":
                        # PostgREST style count
                        cur.execute(f"SELECT COUNT(*) as exact_count FROM {self.table}{where_str}", params)
                        count_val = cur.fetchone()['exact_count']
                        # se limite 1 for passado com count, às vezes eles só querem testar
                        return NeonResponse(data=[], count=count_val)
                    else:
                        cur.execute(f"SELECT {self.columns} FROM {self.table}{where_str}{limit_str}", params)
                        data = cur.fetchall()
                        return NeonResponse(data=[dict(r) for r in data])
                
                elif self.action == "delete":
                    cur.execute(f"DELETE FROM {self.table}{where_str}", params)
                    return NeonResponse(data=[])
                
                elif self.action == "insert":
                    if not self._data:
                        return NeonResponse(data=[])
                    keys = list(self._data[0].keys())
                    columns_str = ", ".join(keys)
                    
                    values = []
                    for row in self._data:
                        row_vals = []
                        for k in keys:
                            val = row.get(k)
                            if isinstance(val, (dict, list)):
                                val = json.dumps(val)
                            row_vals.append(val)
                        values.append(tuple(row_vals))

                    insert_query = f"INSERT INTO {self.table} ({columns_str}) VALUES %s RETURNING id"
                    execute_values(cur, insert_query, values)
                    ids = cur.fetchall()
                    return NeonResponse(data=[dict(r) for r in ids])

class NeonClient:
    def table(self, table_name):
        return NeonQueryBuilder(table_name)

    def rpc(self, rpc_name, params=None):
        class RpcExecutable:
            def execute(self):
                with get_db_connection() as conn:
                    with conn.cursor(cursor_factory=RealDictCursor) as cur:
                        if not params:
                            cur.execute(f"SELECT * FROM {rpc_name}()")
                        else:
                            # Constrói chamada RPC com parâmetros nomeados
                            param_str = ", ".join([f"{k} := %s" for k in params.keys()])
                            cur.execute(f"SELECT * FROM {rpc_name}({param_str})", list(params.values()))
                        data = cur.fetchall()
                        return NeonResponse(data=[dict(r) for r in data])
        return RpcExecutable()

neon_db = NeonClient()
