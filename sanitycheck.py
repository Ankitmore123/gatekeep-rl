import redis

# 1. The Connection
r = redis.Redis(host='localhost', port=6379, db=0, decode_responses=True)

# 2. The Ping (Test Connection)
try:
    if r.ping():
        print("Successfully connected to Redis!")
except redis.ConnectionError:
    print("Failed to connect to Redis.")

# 3. The Operations (Set, Get, Delete)
try:
    # SET: Write a key-value pair into Redis
    r.set('test_key', 'hello_redis')
    
    # GET: Read the value back from Redis
    value = r.get('test_key')
    print(f"The value of test_key is: {value}")
    
    # DELETE: Remove the key from Redis
    r.delete('test_key')
    print("test_key has been deleted.")

except Exception as e:
    print(f"An error occurred during operations: {e}")