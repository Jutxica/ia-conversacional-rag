import os
import oracledb

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
WALLET_DIR = os.path.join(BASE_DIR, "wallet")

DB_USER = "admin"
DB_PASSWORD = "@Mualilissa22"

CONNECT_STRING = '(description= (retry_count=20)(retry_delay=3)(address=(protocol=tcps)(port=1522)(host=adb.sa-saopaulo-1.oraclecloud.com))(connect_data=(service_name=g071d809dc36d2d_dehonai_high.adb.oraclecloud.com))(security=(ssl_server_dn_match=yes)))'

print(f"Connecting to {CONNECT_STRING}")
try:
    pool = oracledb.create_pool(
        user=DB_USER,
        password=DB_PASSWORD,
        dsn=CONNECT_STRING,
        config_dir=WALLET_DIR,
        wallet_location=WALLET_DIR,
        wallet_password=DB_PASSWORD
    )
    with pool.acquire() as connection:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1 FROM DUAL")
            result = cursor.fetchone()
            if result:
                print(f"Connected successfully! Query result: {result[0]}")
except Exception as e:
    import traceback
    traceback.print_exc()

