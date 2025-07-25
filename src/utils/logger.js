// 간단한 로거 유틸리티
class Logger {
  constructor(level = 'info') {
    this.level = level;
    this.levels = {
      error: 0,
      warn: 1,
      info: 2,
      debug: 3
    };
  }

  log(level, message, data = null) {
    // Add validation for 'level'
    if (typeof level !== 'string' || !(level in this.levels)) {
      console.error(`Invalid log level: ${level}. Defaulting to 'info'.`);
      level = 'info'; // Default to a valid level
    }

    if (this.levels[level] <= this.levels[this.level]) {
      const timestamp = new Date().toISOString();
      const logEntry = {
        timestamp,
        level: level.toUpperCase(), // This will now always be safe
        message,
        ...(data && { data })
      };
      
      console.log(JSON.stringify(logEntry));
    }
  }

  error(message, data = null) {
    this.log('error', message, data);
  }

  warn(message, data = null) {
    this.log('warn', message, data);
  }

  info(message, data = null) {
    this.log('info', message, data);
  }

  debug(message, data = null) {
    this.log('debug', message, data);
  }
}

module.exports = new Logger(process.env.LOG_LEVEL || 'info');