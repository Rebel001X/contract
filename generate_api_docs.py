#!/usr/bin/env python3
"""
API文档生成脚本
生成多种格式的API文档
"""

import json
import requests
import os
from pathlib import Path

def generate_openapi_json():
    """生成OpenAPI JSON文档"""
    try:
        # 获取OpenAPI规范
        response = requests.get("http://localhost:8001/openapi.json")
        response.raise_for_status()
        
        # 保存到文件
        with open("openapi.json", "w", encoding="utf-8") as f:
            json.dump(response.json(), f, indent=2, ensure_ascii=False)
        
        print("✅ OpenAPI JSON文档已生成: openapi.json")
        return response.json()
        
    except requests.exceptions.RequestException as e:
        print(f"❌ 无法连接到服务器: {e}")
        print("请确保服务器正在运行: python start_server.py")
        return None

def generate_markdown_docs(openapi_spec):
    """生成Markdown格式的API文档"""
    if not openapi_spec:
        return
    
    md_content = f"""# {openapi_spec['info']['title']} API文档

## 基本信息

- **服务地址**: http://localhost:8001
- **版本**: {openapi_spec['info']['version']}
- **描述**: {openapi_spec['info']['description']}

## 接口列表

"""
    
    # 生成接口文档
    for path, methods in openapi_spec['paths'].items():
        for method, operation in methods.items():
            md_content += f"### {operation.get('summary', '未命名接口')}\n\n"
            md_content += f"- **路径**: `{method.upper()} {path}`\n"
            md_content += f"- **描述**: {operation.get('description', '无描述')}\n\n"
            
            # 请求参数
            if 'parameters' in operation:
                md_content += "**路径参数**:\n\n"
                for param in operation['parameters']:
                    # 兼容各种schema类型
                    schema = param.get('schema', {})
                    if 'type' in schema:
                        param_type = schema['type']
                    elif '$ref' in schema:
                        param_type = schema['$ref'].split('/')[-1]
                    elif 'anyOf' in schema:
                        param_type = ' | '.join([o.get('type', 'any') for o in schema['anyOf']])
                    else:
                        param_type = 'any'
                    md_content += f"- `{param['name']}` ({param_type}) - {param.get('description', '无描述')}\n"
                md_content += "\n"
            
            # 请求体
            if 'requestBody' in operation:
                md_content += "**请求体**:\n\n"
                if 'application/json' in operation['requestBody']['content']:
                    schema = operation['requestBody']['content']['application/json']['schema']
                    if '$ref' in schema:
                        ref_name = schema['$ref'].split('/')[-1]
                        if ref_name in openapi_spec['components']['schemas']:
                            ref_schema = openapi_spec['components']['schemas'][ref_name]
                            md_content += "```json\n"
                            md_content += json.dumps(ref_schema, indent=2, ensure_ascii=False)
                            md_content += "\n```\n\n"
            
            # 响应
            if '200' in operation['responses']:
                md_content += "**响应示例**:\n\n"
                md_content += "```json\n"
                md_content += "{\n"
                md_content += '  "status": "success"\n'
                md_content += "}\n"
                md_content += "```\n\n"
            
            md_content += "---\n\n"
    
    # 保存Markdown文档
    with open("API_DOCUMENTATION.md", "w", encoding="utf-8") as f:
        f.write(md_content)
    
    print("✅ Markdown文档已生成: API_DOCUMENTATION.md")

def generate_typescript_types(openapi_spec):
    """生成TypeScript类型定义"""
    if not openapi_spec:
        return
    
    ts_content = """// 合同审计系统 API 类型定义
// 自动生成，请勿手动修改

"""
    
    # 生成类型定义
    for name, schema in openapi_spec['components']['schemas'].items():
        ts_content += f"export interface {name} {{\n"
        
        if 'properties' in schema:
            for prop_name, prop_schema in schema['properties'].items():
                # 处理类型
                ts_type = 'any'  # 默认类型
                
                if 'type' in prop_schema:
                    if prop_schema['type'] == 'string':
                        ts_type = 'string'
                    elif prop_schema['type'] == 'integer':
                        ts_type = 'number'
                    elif prop_schema['type'] == 'boolean':
                        ts_type = 'boolean'
                    elif prop_schema['type'] == 'array':
                        ts_type = 'any[]'
                elif 'anyOf' in prop_schema:
                    # 处理联合类型
                    types = []
                    for option in prop_schema['anyOf']:
                        if 'type' in option:
                            if option['type'] == 'string':
                                types.append('string')
                            elif option['type'] == 'null':
                                types.append('null')
                    ts_type = ' | '.join(types) if types else 'any'
                
                # 处理可选属性
                required = schema.get('required', [])
                optional = '' if prop_name in required else '?'
                
                ts_content += f"  {prop_name}{optional}: {ts_type};\n"
        
        ts_content += "}\n\n"
    
    # 保存TypeScript文件
    with open("api-types.ts", "w", encoding="utf-8") as f:
        f.write(ts_content)
    
    print("✅ TypeScript类型定义已生成: api-types.ts")

def generate_postman_collection(openapi_spec):
    """生成Postman集合"""
    if not openapi_spec:
        return
    
    collection = {
        "info": {
            "name": openapi_spec['info']['title'],
            "description": openapi_spec['info']['description'],
            "schema": "https://schema.getpostman.com/json/collection/v2.1.0/collection.json"
        },
        "item": []
    }
    
    # 生成请求项
    for path, methods in openapi_spec['paths'].items():
        for method, operation in methods.items():
            item = {
                "name": operation.get('summary', '未命名接口'),
                "request": {
                    "method": method.upper(),
                    "header": [
                        {
                            "key": "Content-Type",
                            "value": "application/json"
                        }
                    ],
                    "url": {
                        "raw": f"{{baseUrl}}{path}",
                        "host": ["{{baseUrl}}"],
                        "path": path.strip('/').split('/')
                    }
                }
            }
            
            # 添加请求体
            if 'requestBody' in operation:
                if 'application/json' in operation['requestBody']['content']:
                    schema = operation['requestBody']['content']['application/json']['schema']
                    if '$ref' in schema:
                        ref_name = schema['$ref'].split('/')[-1]
                        if ref_name in openapi_spec['components']['schemas']:
                            ref_schema = openapi_spec['components']['schemas'][ref_name]
                            # 生成示例数据
                            example = generate_example_data(ref_schema, openapi_spec)
                            item["request"]["body"] = {
                                "mode": "raw",
                                "raw": json.dumps(example, indent=2, ensure_ascii=False)
                            }
            
            collection["item"].append(item)
    
    # 添加变量
    collection["variable"] = [
        {
            "key": "baseUrl",
            "value": "http://localhost:8001"
        }
    ]
    
    # 保存Postman集合
    with open("ContractAudit_API.postman_collection.json", "w", encoding="utf-8") as f:
        json.dump(collection, f, indent=2, ensure_ascii=False)
    
    print("✅ Postman集合已生成: ContractAudit_API.postman_collection.json")

def generate_example_data(schema, openapi_spec):
    """生成示例数据"""
    example = {}
    
    if 'properties' in schema:
        for prop_name, prop_schema in schema['properties'].items():
            if 'type' in prop_schema:
                if prop_schema['type'] == 'string':
                    example[prop_name] = f"示例{prop_name}"
                elif prop_schema['type'] == 'integer':
                    example[prop_name] = 1
                elif prop_schema['type'] == 'boolean':
                    example[prop_name] = False
                elif prop_schema['type'] == 'array':
                    example[prop_name] = []
            elif 'anyOf' in prop_schema:
                # 选择第一个非null类型
                for option in prop_schema['anyOf']:
                    if option['type'] != 'null':
                        if option['type'] == 'string':
                            example[prop_name] = f"示例{prop_name}"
                        elif option['type'] == 'integer':
                            example[prop_name] = 1
                        elif option['type'] == 'boolean':
                            example[prop_name] = False
                        break
                else:
                    example[prop_name] = None
    
    return example

def main():
    """主函数"""
    print("🚀 开始生成API文档...")
    
    # 检查服务器是否运行
    try:
        response = requests.get("http://localhost:8001/health", timeout=5)
        if response.status_code != 200:
            print("❌ 服务器响应异常")
            return
    except requests.exceptions.RequestException:
        print("❌ 无法连接到服务器，请先启动服务器:")
        print("   python start_server.py")
        return
    
    # 生成各种格式的文档
    openapi_spec = generate_openapi_json()
    generate_markdown_docs(openapi_spec)
    generate_typescript_types(openapi_spec)
    generate_postman_collection(openapi_spec)
    
    print("\n🎉 API文档生成完成！")
    print("\n生成的文件:")
    print("- openapi.json (OpenAPI规范)")
    print("- API_DOCUMENTATION.md (Markdown文档)")
    print("- api-types.ts (TypeScript类型)")
    print("- ContractAudit_API.postman_collection.json (Postman集合)")
    print("\n您也可以访问 http://localhost:8001/docs 查看Swagger UI")

if __name__ == "__main__":
    main() 