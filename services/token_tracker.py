# services/token_tracker.py
"""
Token Tracking Service - Theo dõi số token được sử dụng bởi AI Gemini
"""

class TokenTracker:
    """Lớp theo dõi token được sử dụng trong các cuộc gọi Gemini API"""
    
    def __init__(self):
        self.reset()
    
    def reset(self):
        """Xóa tất cả thống kê token"""
        self.stats = {
            "transcribe": {"input": 0, "output": 0, "total": 0},
            "trend_analysis": {"input": 0, "output": 0, "total": 0},
            "content_writing": {"input": 0, "output": 0, "total": 0},
            "image_prompt": {"input": 0, "output": 0, "total": 0},
            "image_generation": {"input": 0, "output": 0, "total": 0},
        }
    
    def add_tokens(self, operation, input_tokens=0, output_tokens=0):
        """
        Thêm số token cho một hoạt động cụ thể
        
        Args:
            operation: Tên hoạt động (transcribe, trend_analysis, content_writing, image_prompt)
            input_tokens: Số token đầu vào
            output_tokens: Số token đầu ra
        """
        if operation not in self.stats:
            self.stats[operation] = {"input": 0, "output": 0, "total": 0}
        
        self.stats[operation]["input"] += input_tokens
        self.stats[operation]["output"] += output_tokens
        self.stats[operation]["total"] += input_tokens + output_tokens
    
    def get_total_tokens(self):
        """Lấy tổng số token đã sử dụng"""
        total = 0
        for operation in self.stats.values():
            total += operation["total"]
        return total
    
    def get_operation_tokens(self, operation):
        """Lấy token cho một hoạt động cụ thể"""
        return self.stats.get(operation, {"input": 0, "output": 0, "total": 0})
    
    def get_all_stats(self):
        """Lấy tất cả thống kê"""
        total = self.get_total_tokens()
        return {
            "total": total,
            "by_operation": self.stats
        }
    
    def get_stats_text(self):
        """Lấy văn bản thống kê token"""
        stats = self.get_all_stats()
        total = stats["total"]
        
        text = f"📊 Tổng Token Sử Dụng: {total:,}\n\n"
        text += "Chi tiết:\n"
        
        for op_name, op_stats in stats["by_operation"].items():
            if op_stats["total"] > 0:
                display_name = self._get_operation_display_name(op_name)
                text += f"  • {display_name}: {op_stats['total']:,} "
                text += f"(Input: {op_stats['input']:,}, Output: {op_stats['output']:,})\n"
        
        return text
    
    @staticmethod
    def _get_operation_display_name(op_name):
        """Chuyển tên hoạt động thành tên hiển thị"""
        mapping = {
            "transcribe": "Nhận dạng giọng nói",
            "trend_analysis": "Phân tích Trend",
            "content_writing": "Viết Content",
            "image_prompt": "Tạo Prompt Ảnh",
            "image_generation": "Tạo Ảnh AI"
        }

        return mapping.get(op_name, op_name)
    
    def estimate_tokens_for_text(self, text):
        """
        Ước tính số token cho một đoạn text
        (Google Gemini: ~1 token ≈ 4 ký tự trung bình)
        
        Args:
            text: Đoạn text cần ước tính
            
        Returns:
            Số token ước tính
        """
        if not text:
            return 0
        # Ước tính: 1 token ≈ 4 ký tự (cho tiếng Anh)
        # Cho tiếng Việt: chia 3 (vì mỗi ký tự Việt phức tạp hơn)
        char_count = len(text)
        # Sử dụng 3.5 để tính cả tiếng Việt và tiếng Anh
        return max(1, char_count // 3)
