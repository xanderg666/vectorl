import oracledb

conn = oracledb.connect(
    user='admin',
    password='Welcome123456$',
    dsn='(description=(retry_count=20)(retry_delay=3)(address=(protocol=tcps)(port=1522)(host=jeszxk0d.adb.sa-bogota-1.oraclecloud.com))(connect_data=(service_name=g1cde62092a80c9_agent2_medium.adb.oraclecloud.com))(security=(ssl_server_dn_match=yes)))'
)
print(f"✓ Conectado: {conn.version}")
conn.close()