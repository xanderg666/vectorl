BEGIN
   DBMS_VECTOR.drop_credential(credential_name => 'OCI_CREDENTIAL_VECTOR');
   COMMIT;
 END;
 /

declare
  jo json_object_t;
begin
  jo := json_object_t();
  jo.put('user_ocid', 'ocid1.user.oc1..aaaaaaaa3uc3z7hultdy7edc5aqsubjekxidutjpyxljssciv4wcmydesz4q');
  jo.put('tenancy_ocid', 'ocid1.tenancy.oc1..aaaaaaaaoi6b5sxlv4z773boczybqz3h2vspvvru42jysvizl77lky22ijaq');
  jo.put('compartment_ocid', 'ocid1.compartment.oc1..aaaaaaaadrmmiknudkmzomyaqwmm6js7ed4sj23jkw7w7ugzgm7cdedsfcua');
  jo.put('private_key', 'MIIEpQIBAAKCAQEAywY4fTOB/5KXjCXGeYreHFiTOkiwoD9rFIAvx2zBTCgo/k5o
OpyyUqw33E0HQSrHbr3b8WRyju/bholJPPU11hXdonZKGSb4zNcRHQJKP668yyKH
PRNkHiRil+ienoZhhKwwvF+M2rZtTkac0I7y5nqMSLd5ncMgVz0U1mgIZ5Z+U9hw
J3LKPsSXET0tX1Mc1PsqSi6Opfv4ZtxHpqVN4IHP01jltzJ0fUdwhWpAER0P0zj7
5H1I122KAD7gILdTg10unkpJ1KhbqSgwchCnnQIDAQABAoIBABzv5QtLVSMVRM5v
7+sQ9Pl7UnjDNZGRmHSSlLzK7n4pVzZv/IEmJnCMJWYcAIW0UDqjiv7L/1wKKfLy
DGNI3AS');
  jo.put('fingerprint', '33:46:af:fe:11:c3:28:3a:65:c2:2f:de:92:34:d6:93');
  DBMS_OUTPUT.put_line(jo.to_string);
  DBMS_VECTOR.create_credential(
    credential_name => 'OCI_CREDENTIAL_VECTOR',
    params => json(jo.to_string));
end;
/

-- ojo en admin

BEGIN
  DBMS_NETWORK_ACL_ADMIN.APPEND_HOST_ACE(
    host => '*',
    ace => xs$ace_type(
      privilege_list => xs$name_list('connect'),
      principal_name => 'AGENTE',  -- ← CAMBIADO DE 'ADMIN' A 'AGENTE'
      principal_type => xs_acl.ptype_db
    )
  );
  COMMIT;
  DBMS_OUTPUT.put_line('✓ Permisos de red (ACL) otorgados al usuario AGENTE');
END;
/

-- ============================================================
-- 3. VERIFICAR LA CREDENCIAL CREADA
-- ============================================================
SELECT credential_name, username, comments
FROM user_credentials
WHERE credential_name = 'OCI_CREDENTIAL_VECTOR';


