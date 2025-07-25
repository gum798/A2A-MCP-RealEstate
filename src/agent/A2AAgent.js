const { v4: uuidv4 } = require('uuid');
const axios = require('axios');

class A2AAgent {
  constructor(agentId, agentName) {
    this.agentId = agentId || uuidv4();
    this.agentName = agentName || 'A2A_Agent';
    this.connections = new Map();
    this.messageQueue = [];
    this.status = 'active';
  }

  // 다른 에이전트와 연결 설정
  async connect(targetAgentUrl, targetAgentId) {
    try {
      const response = await axios.post(`${targetAgentUrl}/api/agent/handshake`, {
        sourceAgentId: this.agentId,
        sourceAgentName: this.agentName,
        timestamp: new Date().toISOString()
      });

      if (response.status === 200) {
        this.connections.set(targetAgentId, {
          url: targetAgentUrl,
          agentId: targetAgentId,
          status: 'connected',
          lastPing: new Date()
        });
        
        console.log(`Connected to agent ${targetAgentId} at ${targetAgentUrl}`);
        return true;
      }
    } catch (error) {
      console.error(`Failed to connect to ${targetAgentUrl}:`, error.message);
      return false;
    }
  }

  // 메시지 전송
  async sendMessage(targetAgentId, messageType, payload) {
    const connection = this.connections.get(targetAgentId);
    
    if (!connection) {
      throw new Error(`No connection found for agent ${targetAgentId}`);
    }

    const message = {
      id: uuidv4(),
      sourceAgentId: this.agentId,
      targetAgentId: targetAgentId,
      messageType: messageType,
      payload: payload,
      timestamp: new Date().toISOString()
    };

    try {
      const response = await axios.post(`${connection.url}/api/agent/message`, message);
      console.log(`Message sent to ${targetAgentId}:`, message.id);
      return response.data;
    } catch (error) {
      console.error(`Failed to send message to ${targetAgentId}:`, error.message);
      throw error;
    }
  }

  // 메시지 수신 처리
  receiveMessage(message) {
    console.log(`Received message from ${message.sourceAgentId}:`, message.id);
    
    // 메시지 큐에 추가
    this.messageQueue.push({
      ...message,
      receivedAt: new Date().toISOString()
    });

    // 메시지 타입별 처리
    switch (message.messageType) {
      case 'ping':
        return this.handlePing(message);
      case 'data_request':
        return this.handleDataRequest(message);
      case 'data_response':
        return this.handleDataResponse(message);
      default:
        return { status: 'received', messageId: message.id };
    }
  }

  // Ping 메시지 처리
  handlePing(message) {
    return {
      status: 'pong',
      messageId: message.id,
      agentId: this.agentId,
      timestamp: new Date().toISOString()
    };
  }

  // 데이터 요청 처리
  handleDataRequest(message) {
    // 샘플 데이터 반환
    const sampleData = this.getSampleData(message.payload.dataType);
    
    return {
      status: 'data_response',
      messageId: message.id,
      data: sampleData,
      timestamp: new Date().toISOString()
    };
  }

  // 데이터 응답 처리
  handleDataResponse(message) {
    console.log('Received data response:', message.payload);
    return {
      status: 'acknowledged',
      messageId: message.id
    };
  }

  // 샘플 데이터 생성
  getSampleData(dataType) {
    const sampleData = {
      'user_data': [
        { id: 1, name: 'John Doe', email: 'john@example.com' },
        { id: 2, name: 'Jane Smith', email: 'jane@example.com' }
      ],
      'order_data': [
        { orderId: 'ORD001', amount: 100.50, status: 'completed' },
        { orderId: 'ORD002', amount: 250.75, status: 'pending' }
      ],
      'system_status': {
        cpu: '45%',
        memory: '62%',
        disk: '34%',
        uptime: '5 days'
      }
    };

    return sampleData[dataType] || { message: 'No data available for this type' };
  }

  // 에이전트 상태 반환
  getStatus() {
    return {
      agentId: this.agentId,
      agentName: this.agentName,
      status: this.status,
      connections: Array.from(this.connections.values()),
      messageQueue: this.messageQueue.length,
      timestamp: new Date().toISOString()
    };
  }
}

module.exports = A2AAgent;