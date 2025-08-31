/**
 * QMT交易系统 - 外部交易接口测试脚本 (JavaScript版本)
 * 使用HMAC-SHA256签名验证
 */

const crypto = require('crypto');
const https = require('https');
const http = require('http');
const { URL } = require('url');

function generateSignature(method, path, queryString, body, timestamp, clientId, secretKey) {
    // 构建签名字符串
    const signString = `${method}\n${path}\n${queryString}\n${body}\n${timestamp}\n${clientId}`;
    
    // 计算HMAC-SHA256签名
    const signature = crypto
        .createHmac('sha256', secretKey)
        .update(signString)
        .digest('hex');
    
    return signature;
}

function makeRequest(url, options, data) {
    return new Promise((resolve, reject) => {
        const urlObj = new URL(url);
        const isHttps = urlObj.protocol === 'https:';
        const client = isHttps ? https : http;
        
        const requestOptions = {
            hostname: urlObj.hostname,
            port: urlObj.port || (isHttps ? 443 : 80),
            path: urlObj.pathname + urlObj.search,
            method: options.method,
            headers: options.headers,
            timeout: 30000
        };
        
        const req = client.request(requestOptions, (res) => {
            let responseData = '';
            
            res.on('data', (chunk) => {
                responseData += chunk;
            });
            
            res.on('end', () => {
                try {
                    const result = {
                        statusCode: res.statusCode,
                        data: JSON.parse(responseData)
                    };
                    resolve(result);
                } catch (e) {
                    resolve({
                        statusCode: res.statusCode,
                        data: responseData
                    });
                }
            });
        });
        
        req.on('error', (error) => {
            reject(error);
        });
        
        req.on('timeout', () => {
            req.destroy();
            reject(new Error('Request timeout'));
        });
        
        if (data) {
            req.write(JSON.stringify(data, Object.keys(data).sort()));
        }
        
        req.end();
    });
}

async function callOuterTradeApi(operation = 'buy') {
    console.log(`=== 测试单笔${operation}交易接口 ===`);
    
    // 配置信息
    const baseUrl = "http://localhost:9091";
    const clientId = "outer_client_002";
    const secretKey = "qmt_secret_key_zzzz";
    
    // 请求参数
    const method = "POST";
    const path = `/qmt/trade/api/outer/trade/${operation}`;
    const queryString = "";  // 没有查询参数
    
    // 请求体
    const data = {
        trader_index: 0,
        symbol: "000001",
        trade_price: 10.50,
        position_pct: 0.1,  // 10%仓位
        strategy_name: "外部策略测试"
    };
    const body = JSON.stringify(data, Object.keys(data).sort());
    
    // 生成时间戳
    const timestamp = Math.floor(Date.now() / 1000).toString();
    
    // 生成签名
    const signature = generateSignature(method, path, queryString, body, timestamp, clientId, secretKey);
    
    // 构建请求头
    const headers = {
        'Content-Type': 'application/json',
        'X-Client-ID': clientId,
        'X-Timestamp': timestamp,
        'X-Signature': signature
    };
    
    // 发送请求
    const url = `${baseUrl}${path}`;
    try {
        const response = await makeRequest(url, { method: 'POST', headers }, data);
        
        console.log(`状态码: ${response.statusCode}`);
        console.log(`响应:`, response.data);
        
        return response;
    } catch (error) {
        console.error('请求失败:', error.message);
        return null;
    }
}

async function callOuterTradeBatchApi(operation = 'buy') {
    console.log(`\n=== 测试批量${operation}交易接口 ===`);
    
    // 配置信息
    const baseUrl = "http://localhost:9091";
    const clientId = "outer_client_002";
    const secretKey = "qmt_secret_key_zzzz";
    
    // 请求参数
    const method = "POST";
    const path = `/qmt/trade/api/outer/trade/batch/${operation}`;
    const queryString = "";  // 没有查询参数
    
    // 请求体
    const data = {
        symbol: "000001",
        trade_price: 10.50,
        position_pct: 0.1,  // 10%仓位
        strategy_name: "外部批量策略测试"
    };
    const body = JSON.stringify(data, Object.keys(data).sort());
    
    // 生成时间戳
    const timestamp = Math.floor(Date.now() / 1000).toString();
    
    // 生成签名
    const signature = generateSignature(method, path, queryString, body, timestamp, clientId, secretKey);
    
    // 构建请求头
    const headers = {
        'Content-Type': 'application/json',
        'X-Client-ID': clientId,
        'X-Timestamp': timestamp,
        'X-Signature': signature
    };
    
    // 发送请求
    const url = `${baseUrl}${path}`;
    try {
        const response = await makeRequest(url, { method: 'POST', headers }, data);
        
        console.log(`状态码: ${response.statusCode}`);
        console.log(`响应:`, response.data);
        
        return response;
    } catch (error) {
        console.error('请求失败:', error.message);
        return null;
    }
}

async function testDifferentOperations() {
    console.log('\n=== 测试不同操作类型 ===');
    
    const operations = ['buy', 'sell'];
    
    for (const operation of operations) {
        console.log(`\n--- 测试 ${operation} 操作 ---`);
        await callOuterTradeApi(operation);
        
        console.log(`\n--- 测试批量 ${operation} 操作 ---`);
        await callOuterTradeBatchApi(operation);
        
        // 等待一秒避免请求过快
        await new Promise(resolve => setTimeout(resolve, 1000));
    }
}

async function testInvalidSignature() {
    console.log('\n=== 测试无效签名 ===');
    
    // 配置信息
    const baseUrl = "http://localhost:9091";
    const clientId = "outer_client_002";
    
    // 请求参数
    const method = "POST";
    const path = "/qmt/trade/api/outer/trade/buy";
    
    // 请求体
    const data = {
        trader_index: 0,
        symbol: "000001",
        trade_price: 10.50,
        position_pct: 0.1,
        strategy_name: "无效签名测试"
    };
    
    // 生成时间戳
    const timestamp = Math.floor(Date.now() / 1000).toString();
    
    // 构建请求头（使用错误的签名）
    const headers = {
        'Content-Type': 'application/json',
        'X-Client-ID': clientId,
        'X-Timestamp': timestamp,
        'X-Signature': 'invalid_signature_for_testing'
    };
    
    // 发送请求
    const url = `${baseUrl}${path}`;
    try {
        const response = await makeRequest(url, { method: 'POST', headers }, data);
        console.log(`状态码: ${response.statusCode}`);
        console.log(`响应:`, response.data);
    } catch (error) {
        console.error('请求失败:', error.message);
    }
}

async function main() {
    console.log('QMT交易系统 - 外部交易接口测试 (JavaScript版本)');
    console.log('='.repeat(60));
    
    try {
        // 测试单笔买入交易接口
        console.log('\n1. 测试单笔买入交易接口');
        await callOuterTradeApi('buy');
        
        // 测试单笔卖出交易接口
        console.log('\n2. 测试单笔卖出交易接口');
        await callOuterTradeApi('sell');
        
        // 测试批量买入交易接口
        console.log('\n3. 测试批量买入交易接口');
        await callOuterTradeBatchApi('buy');
        
        // 测试批量卖出交易接口
        console.log('\n4. 测试批量卖出交易接口');
        await callOuterTradeBatchApi('sell');
        
        // 测试不同操作类型
        console.log('\n5. 测试不同操作类型');
        await testDifferentOperations();
        
        // 测试无效签名
        console.log('\n6. 测试无效签名');
        await testInvalidSignature();
        
        console.log('\n测试完成！');
    } catch (error) {
        console.error('测试过程中发生错误:', error);
    }
}

if (require.main === module) {
    main();
}

module.exports = {
    generateSignature,
    callOuterTradeApi,
    callOuterTradeBatchApi,
    testDifferentOperations,
    testInvalidSignature
};