

-- Solución más robusta con manejo de caracteres especiales
CREATE OR REPLACE FUNCTION busqueda_vectorial_robust (
  p_query IN VARCHAR2,
  top_k IN NUMBER
) RETURN SYS_REFCURSOR IS
  v_results SYS_REFCURSOR;
  query_vec VECTOR;
BEGIN
  query_vec := dbms_vector.utl_to_embedding(
    p_query,
    json('{
      "provider": "OCIGenAI",
      "credential_name": "OCI_CREDENTIAL_VECTOR",
      "url": "https://inference.generativeai.us-chicago-1.oci.oraclecloud.com/20231130/actions/embedText",
      "model": "cohere.embed-v4.0"
     }')
  );

  OPEN v_results FOR
    SELECT
      DOCID,
      -- Limpiar y normalizar el texto completamente
      REGEXP_REPLACE(
        REGEXP_REPLACE(
          TRANSLATE(
            SUBSTR(BODY, 1, 3500),  -- Limitar longitud
            CHR(10) || CHR(13) || CHR(9) || '"' || CHR(92),  -- \n, \r, tab, ", \
            '     '
          ),
          '[[:cntrl:]]',  -- Eliminar caracteres de control
          ' '
        ),
        '\s{2,}',  -- Múltiples espacios
        ' '
      ) as BODY,
      VECTOR_DISTANCE(vector, query_vec) as SCORE
    FROM
      documentos_vectoriales_genai
    ORDER BY SCORE ASC
    FETCH FIRST top_k ROWS ONLY;

  RETURN v_results;
END busqueda_vectorial_robust;
/


-- probar



DECLARE
  v_cursor SYS_REFCURSOR;
  v_docid VARCHAR2(500);
  v_body VARCHAR2(4000);
  v_score NUMBER;
BEGIN
  -- Llamar función
  v_cursor := busqueda_vectorial_robust('que es bre-b', 3);

  -- Procesar resultados
  LOOP
    FETCH v_cursor INTO v_docid, v_body, v_score;
    EXIT WHEN v_cursor%NOTFOUND;

    DBMS_OUTPUT.PUT_LINE('===================');
    DBMS_OUTPUT.PUT_LINE('DocID: ' || v_docid);
    DBMS_OUTPUT.PUT_LINE('Score: ' || v_score);
    DBMS_OUTPUT.PUT_LINE('Body: ' || SUBSTR(v_body, 1, 200) || '...');
  END LOOP;

  CLOSE v_cursor;
END;
/




