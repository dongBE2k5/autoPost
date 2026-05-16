# config/token_history_manager.py
"""
Token History Manager - Quản lý lịch sử sử dụng token
Lưu và tải token usage history từ cơ sở dữ liệu
"""

import json
import os
import sqlite3
import sys
from datetime import datetime

if getattr(sys, 'frozen', False) or '__compiled__' in globals():
    base_dir = os.path.dirname(os.path.abspath(sys.argv[0]))
else:
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

data_dir = os.path.join(base_dir, 'data')
os.makedirs(data_dir, exist_ok=True)
DEFAULT_DB_PATH = os.path.join(data_dir, 'token_history.db')

class TokenHistoryManager:
    """Quản lý lịch sử token usage"""
    
    def __init__(self, db_path=DEFAULT_DB_PATH):
        self.db_path = db_path
        self.init_db()
    
    def init_db(self):
        """Khởi tạo bảng token_history nếu chưa có"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS token_history (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        timestamp TEXT NOT NULL,
                        total_tokens INTEGER NOT NULL,
                        by_operation TEXT NOT NULL,
                        posts_generated INTEGER DEFAULT 0,
                        videos_processed INTEGER DEFAULT 0,
                        notes TEXT DEFAULT ''
                    )
                ''')
                conn.commit()
        except Exception as e:
            print(f"Lỗi khởi tạo bảng token_history: {e}")
    
    def save_token_usage(self, total_tokens, by_operation, posts_count=0, videos_count=0, notes=""):
        """
        Lưu token usage vào database
        
        Args:
            total_tokens: Tổng token sử dụng
            by_operation: Dict chứa chi tiết token theo từng hoạt động
            posts_count: Số bài viết được tạo
            videos_count: Số video được xử lý
            notes: Ghi chú thêm
        """
        try:
            timestamp = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
            by_operation_json = json.dumps(by_operation, ensure_ascii=False)
            
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT INTO token_history 
                    (timestamp, total_tokens, by_operation, posts_generated, videos_processed, notes)
                    VALUES (?, ?, ?, ?, ?, ?)
                ''', (timestamp, total_tokens, by_operation_json, posts_count, videos_count, notes))
                conn.commit()
            
            return True
        except Exception as e:
            print(f"Lỗi lưu token usage: {e}")
            return False
    
    def get_all_history(self):
        """Lấy tất cả lịch sử token usage"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT id, timestamp, total_tokens, by_operation, posts_generated, videos_processed, notes
                    FROM token_history
                    ORDER BY id DESC
                ''')
                rows = cursor.fetchall()
            
            history = []
            for row in rows:
                record = {
                    "id": row[0],
                    "timestamp": row[1],
                    "total_tokens": row[2],
                    "by_operation": json.loads(row[3]) if row[3] else {},
                    "posts_generated": row[4],
                    "videos_processed": row[5],
                    "notes": row[6]
                }
                history.append(record)
            
            return history
        except Exception as e:
            print(f"Lỗi tải token history: {e}")
            return []
    
    def get_history_detailed(self):
        """Lấy lịch sử chi tiết (mở rộng thành từng hoạt động)"""
        try:
            history = self.get_all_history()
            detailed = []
            
            for record in history:
                by_op = record.get("by_operation", {})
                
                for op_name, op_data in by_op.items():
                    if op_data.get("total", 0) > 0:
                        detailed.append({
                            "timestamp": record["timestamp"],
                            "operation": op_name,
                            "input": op_data.get("input", 0),
                            "output": op_data.get("output", 0),
                            "total": op_data.get("total", 0),
                            "posts_generated": record["posts_generated"],
                            "videos_processed": record["videos_processed"]
                        })
            
            return detailed
        except Exception as e:
            print(f"Lỗi tải token history chi tiết: {e}")
            return []
    
    def get_total_all_time(self):
        """Tính tổng token sử dụng từ trước đến nay"""
        try:
            history = self.get_all_history()
            return sum(record.get("total_tokens", 0) for record in history)
        except Exception as e:
            print(f"Lỗi tính tổng token: {e}")
            return 0
    
    def get_summary_stats(self):
        """Lấy thống kê tóm tắt"""
        try:
            history = self.get_all_history()
            
            total_tokens = sum(r.get("total_tokens", 0) for r in history)
            total_posts = sum(r.get("posts_generated", 0) for r in history)
            total_videos = sum(r.get("videos_processed", 0) for r in history)
            
            # Tính trung bình token per post
            avg_token_per_post = total_tokens / total_posts if total_posts > 0 else 0
            
            # Tính token by operation (tổng hợp)
            op_totals = {}
            for record in history:
                by_op = record.get("by_operation", {})
                for op_name, op_data in by_op.items():
                    if op_name not in op_totals:
                        op_totals[op_name] = {"input": 0, "output": 0, "total": 0}
                    op_totals[op_name]["input"] += op_data.get("input", 0)
                    op_totals[op_name]["output"] += op_data.get("output", 0)
                    op_totals[op_name]["total"] += op_data.get("total", 0)
            
            return {
                "total_tokens": total_tokens,
                "total_posts": total_posts,
                "total_videos": total_videos,
                "avg_token_per_post": round(avg_token_per_post),
                "operation_totals": op_totals,
                "num_runs": len(history)
            }
        except Exception as e:
            print(f"Lỗi tính thống kê tóm tắt: {e}")
            return {
                "total_tokens": 0,
                "total_posts": 0,
                "total_videos": 0,
                "avg_token_per_post": 0,
                "operation_totals": {},
                "num_runs": 0
            }
    
    def clear_history(self):
        """Xóa toàn bộ lịch sử token"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("DELETE FROM token_history")
                conn.commit()
            return True
        except Exception as e:
            print(f"Lỗi xóa token history: {e}")
            return False
    
    def delete_record(self, record_id):
        """Xóa một bản ghi cụ thể"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("DELETE FROM token_history WHERE id = ?", (record_id,))
                conn.commit()
            return True
        except Exception as e:
            print(f"Lỗi xóa bản ghi: {e}")
            return False
    
    def export_to_csv(self, filepath):
        """Xuất lịch sử ra file CSV"""
        try:
            import csv
            detailed = self.get_history_detailed()
            
            with open(filepath, 'w', newline='', encoding='utf-8-sig') as f:
                writer = csv.DictWriter(f, fieldnames=["timestamp", "operation", "input", "output", "total", "posts_generated", "videos_processed"])
                writer.writeheader()
                writer.writerows(detailed)
            
            return True
        except Exception as e:
            print(f"Lỗi xuất CSV: {e}")
            return False
