const express = require('express');
const A2AAgent = require('../agent/A2AAgent');

const router = express.Router();

// 전역 에이전트 인스턴스
const agent = new A2AAgent(
  process.env.AGENT_ID,
  process.env.AGENT_NAME
);

// 핸드셰이크 엔드포인트
router.post('/handshake', (req, res) => {
  const { sourceAgentId, sourceAgentName, timestamp } = req.body;
  
  console.log(`Handshake request from ${sourceAgentName} (${sourceAgentId})`);
  
  res.json({
    status: 'handshake_accepted',
    targetAgentId: agent.agentId,
    targetAgentName: agent.agentName,
    timestamp: new Date().toISOString()
  });
});

// 메시지 수신 엔드포인트
router.post('/message', (req, res) => {
  try {
    const response = agent.receiveMessage(req.body);
    res.json(response);
  } catch (error) {
    console.error('Error processing message:', error);
    res.status(500).json({
      error: 'Failed to process message',
      messageId: req.body.id
    });
  }
});

// 연결 설정 엔드포인트
router.post('/connect', async (req, res) => {
  const { targetAgentUrl, targetAgentId } = req.body;
  
  try {
    const success = await agent.connect(targetAgentUrl, targetAgentId);
    
    if (success) {
      res.json({
        status: 'connection_established',
        targetAgentId: targetAgentId,
        targetAgentUrl: targetAgentUrl
      });
    } else {
      res.status(400).json({
        error: 'Failed to establish connection',
        targetAgentId: targetAgentId
      });
    }
  } catch (error) {
    res.status(500).json({
      error: 'Connection error',
      message: error.message
    });
  }
});

// 메시지 전송 엔드포인트
router.post('/send', async (req, res) => {
  const { targetAgentId, messageType, payload } = req.body;
  
  try {
    const response = await agent.sendMessage(targetAgentId, messageType, payload);
    res.json({
      status: 'message_sent',
      response: response
    });
  } catch (error) {
    res.status(500).json({
      error: 'Failed to send message',
      message: error.message
    });
  }
});

// 에이전트 상태 조회
router.get('/status', (req, res) => {
  res.json(agent.getStatus());
});

// Ping 테스트
router.post('/ping/:targetAgentId', async (req, res) => {
  const { targetAgentId } = req.params;
  
  try {
    const response = await agent.sendMessage(targetAgentId, 'ping', {
      message: 'ping test'
    });
    
    res.json({
      status: 'ping_sent',
      response: response
    });
  } catch (error) {
    res.status(500).json({
      error: 'Ping failed',
      message: error.message
    });
  }
});

module.exports = router;