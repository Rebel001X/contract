#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import os
from sqlalchemy import text

# 添加项目路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def check_table_structure():
    """检查数据库表结构"""
    try:
        print("检查数据库表结构...")
        
        # 导入配置
        from ContractAudit.config import engine
        
        # 检查表结构
        with engine.connect() as conn:
            # 检查表是否存在
            result = conn.execute(text("SHOW TABLES LIKE 'confirm_review_rule_result'"))
            tables = result.fetchall()
            if not tables:
                print("❌ 表 confirm_review_rule_result 不存在")
                return False
            
            print("✅ 表 confirm_review_rule_result 存在")
            
            # 检查表结构
            result = conn.execute(text("DESCRIBE confirm_review_rule_result"))
            columns = result.fetchall()
            
            print("\n表结构:")
            print("-" * 80)
            print(f"{'字段名':<20} {'类型':<20} {'是否为空':<10} {'键':<10} {'默认值':<15} {'注释'}")
            print("-" * 80)
            
            has_user_feedback = False
            has_like_count = False
            has_dislike_count = False
            
            for col in columns:
                field_name = col[0]
                field_type = col[1]
                is_null = col[2]
                key = col[3]
                default = col[4] if col[4] else ''
                comment = col[5] if col[5] else ''
                
                print(f"{field_name:<20} {field_type:<20} {is_null:<10} {key:<10} {default:<15} {comment}")
                
                if field_name == 'user_feedback':
                    has_user_feedback = True
                elif field_name == 'like_count':
                    has_like_count = True
                elif field_name == 'dislike_count':
                    has_dislike_count = True
            
            print("-" * 80)
            
            # 分析结果
            if has_user_feedback:
                print("✅ user_feedback 字段已存在")
            else:
                print("❌ user_feedback 字段不存在")
            
            if has_like_count:
                print("⚠️  like_count 字段仍存在（需要删除）")
            else:
                print("✅ like_count 字段已删除")
            
            if has_dislike_count:
                print("⚠️  dislike_count 字段仍存在（需要删除）")
            else:
                print("✅ dislike_count 字段已删除")
            
            return True
        
    except Exception as e:
        print(f"❌ 检查表结构失败: {e}")
        import traceback
        print(f"详细错误信息: {traceback.format_exc()}")
        return False

if __name__ == "__main__":
    success = check_table_structure()
    sys.exit(0 if success else 1) 