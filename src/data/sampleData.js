// 샘플 데이터 모듈
const sampleData = {
  users: [
    {
      id: 1,
      name: "김철수",
      email: "kim.chulsoo@example.com",
      role: "admin",
      department: "IT",
      createdAt: "2024-01-15T09:00:00Z",
      isActive: true
    },
    {
      id: 2,
      name: "이영희",
      email: "lee.younghee@example.com",
      role: "user",
      department: "Sales",
      createdAt: "2024-02-10T14:30:00Z",
      isActive: true
    },
    {
      id: 3,
      name: "박민수",
      email: "park.minsoo@example.com",
      role: "manager",
      department: "Marketing",
      createdAt: "2024-01-20T11:15:00Z",
      isActive: false
    },
    {
      id: 4,
      name: "정수연",
      email: "jung.suyeon@example.com",
      role: "user",
      department: "HR",
      createdAt: "2024-03-05T16:45:00Z",
      isActive: true
    }
  ],

  orders: [
    {
      orderId: "ORD-2024-001",
      customerId: 1,
      customerName: "김철수",
      items: [
        { productId: 101, productName: "노트북", quantity: 1, price: 1500000 },
        { productId: 102, productName: "마우스", quantity: 2, price: 25000 }
      ],
      totalAmount: 1550000,
      status: "completed",
      orderDate: "2024-06-01T10:30:00Z",
      deliveryDate: "2024-06-03T14:00:00Z"
    },
    {
      orderId: "ORD-2024-002",
      customerId: 2,
      customerName: "이영희",
      items: [
        { productId: 103, productName: "키보드", quantity: 1, price: 150000 },
        { productId: 104, productName: "모니터", quantity: 1, price: 300000 }
      ],
      totalAmount: 450000,
      status: "pending",
      orderDate: "2024-06-15T15:20:00Z",
      deliveryDate: null
    },
    {
      orderId: "ORD-2024-003",
      customerId: 4,
      customerName: "정수연",
      items: [
        { productId: 105, productName: "태블릿", quantity: 1, price: 800000 }
      ],
      totalAmount: 800000,
      status: "shipped",
      orderDate: "2024-06-20T09:15:00Z",
      deliveryDate: "2024-06-22T16:30:00Z"
    }
  ],

  products: [
    {
      id: 101,
      name: "울트라북 Pro",
      category: "전자제품",
      price: 1500000,
      stock: 15,
      description: "고성능 울트라북",
      specifications: {
        cpu: "Intel i7",
        memory: "16GB",
        storage: "512GB SSD",
        display: "14인치 FHD"
      },
      createdAt: "2024-01-10T08:00:00Z"
    },
    {
      id: 102,
      name: "무선 마우스",
      category: "액세서리",
      price: 25000,
      stock: 50,
      description: "인체공학적 무선 마우스",
      specifications: {
        connectivity: "Bluetooth 5.0",
        battery: "충전식",
        sensor: "광학식"
      },
      createdAt: "2024-01-12T10:30:00Z"
    },
    {
      id: 103,
      name: "기계식 키보드",
      category: "액세서리",
      price: 150000,
      stock: 25,
      description: "RGB 백라이트 기계식 키보드",
      specifications: {
        switch: "체리 MX 브라운",
        layout: "한영 104키",
        backlight: "RGB"
      },
      createdAt: "2024-01-15T14:20:00Z"
    },
    {
      id: 104,
      name: "4K 모니터",
      category: "전자제품",
      price: 300000,
      stock: 8,
      description: "27인치 4K UHD 모니터",
      specifications: {
        size: "27인치",
        resolution: "3840x2160",
        refreshRate: "60Hz",
        panel: "IPS"
      },
      createdAt: "2024-02-01T11:45:00Z"
    },
    {
      id: 105,
      name: "프리미엄 태블릿",
      category: "전자제품",
      price: 800000,
      stock: 12,
      description: "10인치 프리미엄 태블릿",
      specifications: {
        display: "10.5인치 OLED",
        storage: "256GB",
        memory: "8GB",
        os: "Android 14"
      },
      createdAt: "2024-02-15T09:30:00Z"
    }
  ],

  systemStatus: {
    server: {
      name: "A2A_Agent_Server",
      status: "running",
      uptime: "5 days, 12 hours",
      cpu: {
        usage: "45%",
        cores: 8,
        load: [1.2, 1.5, 1.8]
      },
      memory: {
        total: "16GB",
        used: "10GB",
        free: "6GB",
        usage: "62%"
      },
      disk: {
        total: "500GB",
        used: "170GB",
        free: "330GB",
        usage: "34%"
      }
    },
    database: {
      status: "connected",
      type: "PostgreSQL",
      version: "14.9",
      connections: {
        active: 12,
        idle: 8,
        max: 100
      },
      performance: {
        queries_per_second: 145,
        avg_response_time: "12ms"
      }
    },
    network: {
      status: "connected",
      latency: "8ms",
      bandwidth: {
        download: "1Gbps",
        upload: "1Gbps"
      },
      packets: {
        sent: 1254789,
        received: 1198756,
        lost: 0.1
      }
    },
    services: [
      { name: "A2A_Agent", status: "running", port: 3000 },
      { name: "Database", status: "running", port: 5432 },
      { name: "Redis", status: "running", port: 6379 },
      { name: "Message_Queue", status: "running", port: 5672 }
    ],
    lastUpdate: "2024-07-02T17:45:00Z"
  },

  // 실시간 메트릭 데이터
  metrics: {
    requests: {
      total: 15847,
      success: 15234,
      failed: 613,
      rate: "125 req/min"
    },
    response_times: {
      avg: "45ms",
      p50: "32ms",
      p95: "85ms",
      p99: "120ms"
    },
    errors: [
      { type: "timeout", count: 45, last_occurrence: "2024-07-02T17:30:00Z" },
      { type: "connection_refused", count: 12, last_occurrence: "2024-07-02T16:45:00Z" },
      { type: "invalid_request", count: 8, last_occurrence: "2024-07-02T17:20:00Z" }
    ]
  }
};

module.exports = sampleData;