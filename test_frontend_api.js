// 测试前端API调用
const axios = require('axios');

async function testTaskDetailAPI() {
    console.log('=== 测试任务详情API调用 ===');
    
    try {
        // 模拟前端的API调用
        const response = await axios.get('http://localhost:8000/api/v1/tasks/task_2538b12e492e', {
            headers: {
                'Content-Type': 'application/json',
                // 注意：这里没有Authorization token，可能是问题所在
            },
            timeout: 30000
        });
        
        console.log('✅ API调用成功');
        console.log('Status:', response.status);
        console.log('Response structure:');
        console.log({
            success: response.data.success,
            hasData: !!response.data.data,
            taskId: response.data.data?.task_id,
            status: response.data.data?.status
        });
        
        return response.data;
        
    } catch (error) {
        console.log('❌ API调用失败');
        console.log('Error:', error.message);
        
        if (error.response) {
            console.log('Response status:', error.response.status);
            console.log('Response data:', error.response.data);
        } else if (error.request) {
            console.log('No response received');
        } else {
            console.log('Request setup error');
        }
        
        throw error;
    }
}

async function testTaskListAPI() {
    console.log('\n=== 测试任务列表API调用 ===');
    
    try {
        const response = await axios.get('http://localhost:8000/api/v1/tasks', {
            headers: {
                'Content-Type': 'application/json',
            },
            timeout: 30000
        });
        
        console.log('✅ 任务列表API调用成功');
        console.log('Total tasks:', response.data.data?.total || 0);
        console.log('Tasks count:', response.data.data?.items?.length || 0);
        
        if (response.data.data?.items?.length > 0) {
            console.log('First task ID:', response.data.data.items[0].task_id);
        }
        
        return response.data;
        
    } catch (error) {
        console.log('❌ 任务列表API调用失败');
        console.log('Error:', error.message);
        throw error;
    }
}

// 运行测试
async function runTests() {
    try {
        await testTaskListAPI();
        await testTaskDetailAPI();
        console.log('\n🎉 所有API测试通过');
    } catch (error) {
        console.log('\n💥 测试失败，需要检查API连接');
        process.exit(1);
    }
}

runTests();