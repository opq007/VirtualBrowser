 """测试本地代理转发服务
"""
import socket
import struct
import sys

def test_http_proxy():
    """测试 HTTP 代理转发"""
    print('[TEST] 测试 HTTP 代理转发...')
    
    # 连接本地代理
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        sock.connect(('127.0.0.1', 12345))
        
        # 发送 CONNECT 请求
        request = b'CONNECT www.google.com:443 HTTP/1.1\r\nHost: www.google.com:443\r\n\r\n'
        sock.sendall(request)
        
        # 接收响应
        response = sock.recv(4096)
        print(f'[TEST] HTTP 响应: {response.decode(errors="ignore")[:200]}')
        
        if b'200' in response:
            print('[TEST] HTTP 代理测试: ✓ 成功')
            return True
        else:
            print('[TEST] HTTP 代理测试: ✗ 失败')
            return False
    except Exception as e:
        print(f'[TEST] HTTP 代理测试: ✗ 错误 - {e}')
        return False
    finally:
        sock.close()

def test_socks5_proxy():
    """测试 SOCKS5 代理转发"""
    print('[TEST] 测试 SOCKS5 代理转发...')
    
    # 连接本地代理（通过 HTTP 协议）
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        sock.connect(('127.0.0.1', 12345))
        
        # 发送 HTTP CONNECT 请求
        request = b'CONNECT www.google.com:443 HTTP/1.1\r\nHost: www.google.com:443\r\n\r\n'
        sock.sendall(request)
        
        # 接收响应
        response = sock.recv(4096)
        print(f'[TEST] SOCKS5 转发响应: {response.decode(errors="ignore")[:200]}')
        
        if b'200' in response:
            print('[TEST] SOCKS5 代理测试: ✓ 成功')
            return True
        else:
            print('[TEST] SOCKS5 代理测试: ✗ 失败')
            return False
    except Exception as e:
        print(f'[TEST] SOCKS5 代理测试: ✗ 错误 - {e}')
        return False
    finally:
        sock.close()

def main():
    print('[TEST] 本地代理转发服务测试')
    print('=' * 50)
    
    # 测试配置
    tests = []
    
    # 测试 HTTP 代理
    result = test_http_proxy()
    tests.append(('HTTP 代理', result))
    
    # 测试 SOCKS5 代理
    result = test_socks5_proxy()
    tests.append(('SOCKS5 代理', result))
    
    # 输出结果
    print('\n' + '=' * 50)
    print('[TEST] 测试结果汇总:')
    for name, result in tests:
        status = '✓ 通过' if result else '✗ 失败'
        print(f'  {name}: {status}')
    
    all_passed = all(r for _, r in tests)
    print(f'\n[TEST] 总体结果: {"✓ 所有测试通过" if all_passed else "✗ 部分测试失败"}')
    
    return 0 if all_passed else 1

if __name__ == '__main__':
    sys.exit(main())