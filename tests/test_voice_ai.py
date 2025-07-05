# tests/test_voice_ai.py

import pytest
from unittest.mock import Mock, patch, AsyncMock
import sys
from pathlib import Path

# Add the parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

from app.voice_ai.twilio import TwilioClient
from app.voice_ai.vapi import VapiClient
from app.voice_ai.retell import RetellClient

# ---------------------------
# TwilioClient Tests
# ---------------------------

class TestTwilioClient:
    """Test Twilio voice AI integration"""

    @pytest.fixture(scope="function")
    def twilio_client(self):
        """Create a Twilio client instance"""
        return TwilioClient(account_sid="test_sid", auth_token="test_token")

    @pytest.mark.asyncio
    async def test_send_sms(self, twilio_client):
        """Test sending SMS via Twilio"""
        with patch.object(twilio_client.client.messages, 'create', return_value=Mock(sid='sms_123')) as mock_create:
            result = await twilio_client.send_sms('+1234567890', 'Test message')
            assert result == 'sms_123'
            mock_create.assert_called_once()

    @pytest.mark.asyncio
    async def test_make_call(self, twilio_client):
        """Test making outbound call via Twilio"""
        with patch.object(twilio_client.client.calls, 'create', return_value=Mock(sid='call_123')) as mock_create:
            result = await twilio_client.make_call('+1234567890', 'Hello world')
            assert result == 'call_123'
            mock_create.assert_called_once()

    @pytest.mark.asyncio
    async def test_process_voice_input(self, twilio_client):
        """Test processing voice input via OpenAI Whisper"""
        with patch('httpx.AsyncClient.get', new_callable=AsyncMock) as mock_get:
            mock_get.return_value.content = b'audio_data'
            with patch.object(twilio_client.openai_client, 'post', new_callable=AsyncMock) as mock_post:
                mock_post.return_value.status_code = 200
                mock_post.return_value.json.return_value = {'text': 'Hello'}
                result = await twilio_client.process_voice_input('https://example.com/audio.wav')
                assert result == 'Hello'

    @pytest.mark.asyncio
    async def test_generate_ai_response(self, twilio_client):
        """Test generating AI response via OpenAI GPT"""
        with patch.object(twilio_client.openai_client, 'post', new_callable=AsyncMock) as mock_post:
            mock_post.return_value.status_code = 200
            mock_post.return_value.json.return_value = {
                'choices': [{ 'message': { 'content': 'AI response' } }]
            }
            response = await twilio_client.generate_ai_response('Hello', [])
            assert response == 'AI response'

# ---------------------------
# VapiClient Tests
# ---------------------------

class TestVapiClient:
    """Test Vapi AI voice integration"""

    @pytest.fixture(scope="function")
    def vapi_client(self):
        """Create a Vapi client instance"""
        return VapiClient(api_key="test_vapi_key")

    @pytest.mark.asyncio
    async def test_make_call(self, vapi_client):
        """Test making a call via Vapi"""
        with patch.object(vapi_client.session, 'post', new_callable=AsyncMock) as mock_post:
            mock_post.return_value.status_code = 200
            mock_post.return_value.json.return_value = {'call_id': 'vapi_call_123'}
            result = await vapi_client.make_call('+1234567890', 'Hello from Vapi')
            assert result == 'vapi_call_123'
            mock_post.assert_called_once()

    @pytest.mark.asyncio
    async def test_send_message(self, vapi_client):
        """Test sending a message via Vapi"""
        with patch.object(vapi_client.session, 'post', new_callable=AsyncMock) as mock_post:
            mock_post.return_value.status_code = 200
            mock_post.return_value.json.return_value = {'message_id': 'vapi_msg_456'}
            result = await vapi_client.send_message('+1234567890', 'Test Vapi message')
            assert result == 'vapi_msg_456'
            mock_post.assert_called_once()

# ---------------------------
# RetellClient Tests
# ---------------------------

class TestRetellClient:
    """Test Retell AI voice integration"""

    @pytest.fixture(scope="function")
    def retell_client(self):
        """Create a Retell client instance"""
        return RetellClient(api_key="test_retell_key")

    @pytest.mark.asyncio
    async def test_initiate_call(self, retell_client):
        """Test initiating a call via Retell"""
        with patch.object(retell_client.session, 'post', new_callable=AsyncMock) as mock_post:
            mock_post.return_value.status_code = 200
            mock_post.return_value.json.return_value = {'call_id': 'retell_call_789'}
            result = await retell_client.initiate_call('+1234567890', 'Hello from Retell')
            assert result == 'retell_call_789'
            mock_post.assert_called_once()

    @pytest.mark.asyncio
    async def test_send_text(self, retell_client):
        """Test sending a text message via Retell"""
        with patch.object(retell_client.session, 'post', new_callable=AsyncMock) as mock_post:
            mock_post.return_value.status_code = 200
            mock_post.return_value.json.return_value = {'message_id': 'retell_msg_321'}
            result = await retell_client.send_text('+1234567890', 'Test Retell message')
            assert result == 'retell_msg_321'
            mock_post.assert_called_once()
