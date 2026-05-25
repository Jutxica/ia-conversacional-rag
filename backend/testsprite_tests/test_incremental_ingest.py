import pytest
from unittest.mock import MagicMock, patch

# Teste para verificar o fluxo de pulo (skip) caso o hash do arquivo seja idêntico
@patch("main.supabase_admin")
def test_upload_identical_hash_skips(mock_supabase):
    # Mock do supabase_admin.table().select().eq().limit().execute()
    mock_select = MagicMock()
    mock_eq = MagicMock()
    mock_limit = MagicMock()
    mock_execute = MagicMock()
    
    # Simula que o arquivo já existe com o mesmo hash
    test_hash = "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855" # hash vazio
    mock_execute.data = [{"metadata": {"file_hash": test_hash}}]
    
    mock_supabase.table.return_value = mock_select
    mock_select.select.return_value = mock_select
    mock_select.eq.return_value = mock_eq
    mock_eq.limit.return_value = mock_limit
    mock_limit.execute.return_value = mock_execute
    
    # Importamos localmente para usar os mocks configurados
    from main import admin_upload
    
    # Mock do UploadFile
    mock_file = MagicMock()
    mock_file.filename = "teste.pdf"
    
    # Criamos uma função corrotina para simular o await file.read()
    async def async_read():
        return b""
    mock_file.read = async_read
    
    import asyncio
    # Executa a função assíncrona
    loop = asyncio.get_event_loop()
    response = loop.run_until_complete(admin_upload(
        file=mock_file,
        title="Teste Doc",
        author="Dehon",
        year="1889",
        category="Diários"
    ))
    
    # O status deve ser "skipped" e chunks_inserted = 0
    assert response["status"] == "skipped"
    assert response["chunks_inserted"] == 0
    assert "Ingestão pulada" in response["message"]
