import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
import heapq
import time
import random
import threading
from typing import List, Tuple, Optional

class PuzzleState:
    """Lớp đại diện cho một trạng thái của puzzle 15"""
    
    def __init__(self, board: List[int], moves: int = 0, parent=None, last_move: str = ''):
        self.board = board[:]
        self.moves = moves
        self.parent = parent
        self.last_move = last_move
        self.empty_pos = self._find_empty()
        self.heuristic = self._calculate_manhattan()
        self.cost = self.moves + self.heuristic
    
    def _find_empty(self) -> Tuple[int, int]:
        """Tìm vị trí ô trống (số 0)"""
        pos = self.board.index(0)
        return (pos // 4, pos % 4)
    
    def _calculate_manhattan(self) -> int:
        """Tính Manhattan Distance - heuristic function"""
        distance = 0
        for i in range(16):
            if self.board[i] != 0:
                current_row, current_col = i // 4, i % 4
                target_row, target_col = (self.board[i] - 1) // 4, (self.board[i] - 1) % 4
                distance += abs(current_row - target_row) + abs(current_col - target_col)
        return distance
    
    def is_goal(self) -> bool:
        """Kiểm tra xem đã đạt trạng thái đích chưa"""
        return self.board == list(range(1, 16)) + [0]
    
    def get_neighbors(self) -> List['PuzzleState']:
        """Tạo các trạng thái kế tiếp có thể đạt được"""
        neighbors = []
        row, col = self.empty_pos
        
        directions = [
            (-1, 0, 'XUỐNG'),
            (1, 0, 'LÊN'),
            (0, -1, 'PHẢI'),
            (0, 1, 'TRÁI')
        ]
        
        for dr, dc, move_name in directions:
            new_row, new_col = row + dr, col + dc
            
            if 0 <= new_row < 4 and 0 <= new_col < 4:
                new_board = self.board[:]
                empty_index = row * 4 + col
                new_index = new_row * 4 + new_col
                
                new_board[empty_index], new_board[new_index] = new_board[new_index], new_board[empty_index]
                
                neighbors.append(PuzzleState(new_board, self.moves + 1, self, 
                                           f"Di chuyển {new_board[empty_index]} {move_name}"))
        
        return neighbors
    
    def __lt__(self, other):
        return self.cost < other.cost
    
    def __eq__(self, other):
        return self.board == other.board
    
    def __hash__(self):
        return hash(tuple(self.board))

class PuzzleSolver:
    """Bộ giải puzzle sử dụng thuật toán A*"""
    
    def __init__(self):
        self.explored_count = 0
        self.max_frontier_size = 0
        self.is_solving = False
    
    def is_solvable(self, board: List[int]) -> bool:
        """Kiểm tra xem puzzle có giải được không"""
        inversions = 0
        flat_board = [x for x in board if x != 0]
        
        for i in range(len(flat_board)):
            for j in range(i + 1, len(flat_board)):
                if flat_board[i] > flat_board[j]:
                    inversions += 1
        
        empty_row = 4 - (board.index(0) // 4)
        
        if empty_row % 2 == 1:
            return inversions % 2 == 0
        else:
            return inversions % 2 == 1
    
    def solve(self, initial_board: List[int], progress_callback=None, stop_callback=None):
        """Giải puzzle bằng thuật toán A*"""
        start_time = time.time()
        self.is_solving = True
            
        if not self.is_solvable(initial_board):
            return None, {
                'solvable': False,
                'time': time.time() - start_time,
                'explored': 0,
                'max_frontier': 0
            }
        
        initial_state = PuzzleState(initial_board)
        
        if initial_state.is_goal():
            return [initial_state], {
                'solvable': True,
                'time': time.time() - start_time,
                'explored': 0,
                'max_frontier': 0,
                'solution_length': 0
            }
        
        frontier = [initial_state]
        heapq.heapify(frontier)
        explored = set()
        
        self.explored_count = 0
        self.max_frontier_size = 0
        
        while frontier and self.is_solving:
            if stop_callback and stop_callback():
                self.is_solving = False
                break
                
            self.max_frontier_size = max(self.max_frontier_size, len(frontier))
            
            current = heapq.heappop(frontier)
            
            if tuple(current.board) in explored:
                continue
            
            explored.add(tuple(current.board))
            self.explored_count += 1
            
            # Callback để cập nhật GUI
            if progress_callback and self.explored_count % 50 == 0:
                progress_callback(self.explored_count, len(frontier), current.heuristic, current.cost)
            
            if current.is_goal():
                path = []
                while current:
                    path.append(current)
                    current = current.parent
                path.reverse()
                
                self.is_solving = False
                return path, {
                    'solvable': True,
                    'time': time.time() - start_time,
                    'explored': self.explored_count,
                    'max_frontier': self.max_frontier_size,
                    'solution_length': len(path) - 1
                }
            
            for neighbor in current.get_neighbors():
                if tuple(neighbor.board) not in explored:
                    heapq.heappush(frontier, neighbor)
        
        self.is_solving = False
        return None, {
            'solvable': False,
            'time': time.time() - start_time,
            'explored': self.explored_count,
            'max_frontier': self.max_frontier_size
        }

class PuzzleGUI:
    """Giao diện đồ họa cho 15-Puzzle"""
    
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("15-Puzzle Solver - Thuật toán A*")
        self.root.geometry("1000x700")
        self.root.configure(bg='#2C3E50')
        
        # Dữ liệu puzzle
        self.current_board = list(range(1, 16)) + [0]
        self.solution_path = []
        self.solver = PuzzleSolver()
        self.is_solving = False
        self.replay_index = 0
        
        # Tạo giao diện
        self.create_widgets()
        self.update_display()
        
    def create_widgets(self):
        """Tạo các widget cho giao diện"""
        
        # Header
        header_frame = tk.Frame(self.root, bg='#2C3E50')
        header_frame.pack(pady=20)
        
        title_label = tk.Label(header_frame, text="🧩 15-PUZZLE SOLVER", 
                              font=('Arial', 24, 'bold'), fg='#ECF0F1', bg='#2C3E50')
        title_label.pack()
        
        subtitle_label = tk.Label(header_frame, text="Giải bài toán 15 ô số bằng Thuật toán A* (Trí tuệ nhân tạo)",
                                 font=('Arial', 12), fg='#BDC3C7', bg='#2C3E50')
        subtitle_label.pack(pady=5)
        
        # Algorithm info
        algo_frame = tk.LabelFrame(self.root, text="🧠 Thuật toán A*", 
                                  font=('Arial', 12, 'bold'), fg='#ECF0F1', bg='#34495E')
        algo_frame.pack(pady=10, padx=20, fill='x')
        
        algo_text = """f(n) = g(n) + h(n)
• g(n): Chi phí từ trạng thái ban đầu đến n (số bước đã đi)
• h(n): Heuristic Manhattan Distance (ước tính đến đích)  
• f(n): Tổng ước tính chi phí để đi qua trạng thái n"""
        
        tk.Label(algo_frame, text=algo_text, font=('Arial', 10), 
                fg='#ECF0F1', bg='#34495E', justify='left').pack(pady=10)
        
        # Main content frame
        main_frame = tk.Frame(self.root, bg='#2C3E50')
        main_frame.pack(expand=True, fill='both', padx=20)
        
        # Left side - Puzzle
        left_frame = tk.Frame(main_frame, bg='#2C3E50')
        left_frame.pack(side='left', fill='both', expand=True)
        
        # Puzzle frame
        puzzle_frame = tk.LabelFrame(left_frame, text="🎯 Bảng Puzzle", 
                                   font=('Arial', 12, 'bold'), fg='#ECF0F1', bg='#34495E')
        puzzle_frame.pack(pady=10, fill='both', expand=True)
        
        # Puzzle grid
        self.puzzle_frame = tk.Frame(puzzle_frame, bg='#34495E')
        self.puzzle_frame.pack(pady=20)
        
        self.buttons = []
        for i in range(16):
            row, col = i // 4, i % 4
            btn = tk.Button(self.puzzle_frame, text="", width=4, height=2,
                           font=('Arial', 16, 'bold'), 
                           command=lambda r=row, c=col: self.tile_clicked(r, c))
            btn.grid(row=row, column=col, padx=2, pady=2)
            self.buttons.append(btn)
        
        # Control buttons
        control_frame = tk.Frame(left_frame, bg='#2C3E50')
        control_frame.pack(pady=10)
        
        self.shuffle_btn = tk.Button(control_frame, text="🎲 Xáo trộn", 
                                   command=self.shuffle_puzzle,
                                   bg='#E74C3C', fg='white', font=('Arial', 10, 'bold'),
                                   padx=20, pady=5)
        self.shuffle_btn.pack(side='left', padx=5)
        
        self.reset_btn = tk.Button(control_frame, text="🔄 Reset",
                                 command=self.reset_puzzle,
                                 bg='#F39C12', fg='white', font=('Arial', 10, 'bold'),
                                 padx=20, pady=5)
        self.reset_btn.pack(side='left', padx=5)
        
        self.demo_btn = tk.Button(control_frame, text="📚 Demo",
                                command=self.load_demo_puzzle,
                                bg='#9B59B6', fg='white', font=('Arial', 10, 'bold'),
                                padx=20, pady=5)
        self.demo_btn.pack(side='left', padx=5)
        
        # Solve button
        self.solve_btn = tk.Button(left_frame, text="🤖 GIẢI BẰNG A* ALGORITHM",
                                 command=self.solve_puzzle,
                                 bg='#27AE60', fg='white', font=('Arial', 12, 'bold'),
                                 pady=10)
        self.solve_btn.pack(pady=20, fill='x')
        
        # Progress bar
        self.progress_var = tk.DoubleVar()
        self.progress_bar = ttk.Progressbar(left_frame, variable=self.progress_var, 
                                          mode='indeterminate')
        
        # Right side - Stats and Solution
        right_frame = tk.Frame(main_frame, bg='#2C3E50')
        right_frame.pack(side='right', fill='both', expand=True, padx=(20, 0))
        
        # Stats frame
        stats_frame = tk.LabelFrame(right_frame, text="📊 Thống kê Thuật toán A*",
                                  font=('Arial', 12, 'bold'), fg='#ECF0F1', bg='#34495E')
        stats_frame.pack(fill='x', pady=10)
        
        # Stats grid
        stats_inner = tk.Frame(stats_frame, bg='#34495E')
        stats_inner.pack(pady=15, padx=10, fill='x')
        
        # Row 1
        tk.Label(stats_inner, text="Trạng thái khám phá:", 
                font=('Arial', 10), fg='#ECF0F1', bg='#34495E').grid(row=0, column=0, sticky='w', pady=5)
        self.explored_label = tk.Label(stats_inner, text="0", 
                                     font=('Arial', 10, 'bold'), fg='#3498DB', bg='#34495E')
        self.explored_label.grid(row=0, column=1, sticky='e', pady=5)
        
        # Row 2
        tk.Label(stats_inner, text="Frontier tối đa:", 
                font=('Arial', 10), fg='#ECF0F1', bg='#34495E').grid(row=1, column=0, sticky='w', pady=5)
        self.frontier_label = tk.Label(stats_inner, text="0", 
                                     font=('Arial', 10, 'bold'), fg='#E74C3C', bg='#34495E')
        self.frontier_label.grid(row=1, column=1, sticky='e', pady=5)
        
        # Row 3
        tk.Label(stats_inner, text="Độ sâu giải pháp:", 
                font=('Arial', 10), fg='#ECF0F1', bg='#34495E').grid(row=2, column=0, sticky='w', pady=5)
        self.depth_label = tk.Label(stats_inner, text="0", 
                                   font=('Arial', 10, 'bold'), fg='#F39C12', bg='#34495E')
        self.depth_label.grid(row=2, column=1, sticky='e', pady=5)
        
        # Row 4
        tk.Label(stats_inner, text="Thời gian thực thi:", 
                font=('Arial', 10), fg='#ECF0F1', bg='#34495E').grid(row=3, column=0, sticky='w', pady=5)
        self.time_label = tk.Label(stats_inner, text="0ms", 
                                  font=('Arial', 10, 'bold'), fg='#27AE60', bg='#34495E')
        self.time_label.grid(row=3, column=1, sticky='e', pady=5)
        
        # Row 5
        tk.Label(stats_inner, text="Manhattan Distance:", 
                font=('Arial', 10), fg='#ECF0F1', bg='#34495E').grid(row=4, column=0, sticky='w', pady=5)
        self.manhattan_label = tk.Label(stats_inner, text="0", 
                                      font=('Arial', 10, 'bold'), fg='#9B59B6', bg='#34495E')
        self.manhattan_label.grid(row=4, column=1, sticky='e', pady=5)
        
        # Row 6
        tk.Label(stats_inner, text="Chi phí hiện tại f(n):", 
                font=('Arial', 10), fg='#ECF0F1', bg='#34495E').grid(row=5, column=0, sticky='w', pady=5)
        self.cost_label = tk.Label(stats_inner, text="0", 
                                  font=('Arial', 10, 'bold'), fg='#E67E22', bg='#34495E')
        self.cost_label.grid(row=5, column=1, sticky='e', pady=5)
        
        # Configure grid weights
        stats_inner.grid_columnconfigure(1, weight=1)
        
        # Solution frame
        solution_frame = tk.LabelFrame(right_frame, text="🎯 Lời giải từng bước",
                                     font=('Arial', 12, 'bold'), fg='#ECF0F1', bg='#34495E')
        solution_frame.pack(fill='both', expand=True, pady=10)
        
        # Solution text area
        self.solution_text = scrolledtext.ScrolledText(solution_frame, height=15, width=40,
                                                      font=('Consolas', 9), 
                                                      bg='#2C3E50', fg='#ECF0F1',
                                                      insertbackground='#ECF0F1')
        self.solution_text.pack(pady=10, padx=10, fill='both', expand=True)
        
        # Replay controls
        replay_frame = tk.Frame(solution_frame, bg='#34495E')
        replay_frame.pack(pady=10)
        
        self.replay_btn = tk.Button(replay_frame, text="🎬 Replay",
                                  command=self.start_replay,
                                  bg='#8E44AD', fg='white', font=('Arial', 10, 'bold'),
                                  state='disabled')
        self.replay_btn.pack(side='left', padx=5)
        
        self.stop_btn = tk.Button(replay_frame, text="⏹️ Dừng",
                                command=self.stop_solving,
                                bg='#E74C3C', fg='white', font=('Arial', 10, 'bold'),
                                state='disabled')
        self.stop_btn.pack(side='left', padx=5)
        
        # Status bar
        self.status_var = tk.StringVar()
        self.status_var.set("Sẵn sàng - Nhấn 'Xáo trộn' để bắt đầu")
        status_bar = tk.Label(self.root, textvariable=self.status_var,
                            font=('Arial', 10), fg='#ECF0F1', bg='#34495E',
                            relief='sunken', anchor='w')
        status_bar.pack(side='bottom', fill='x')
    
    def update_display(self):
        """Cập nhật hiển thị puzzle"""
        for i in range(16):
            btn = self.buttons[i]
            value = self.current_board[i]
            
            if value == 0:
                btn.config(text="", bg='#7F8C8D', state='disabled',
                          relief='sunken')
            else:
                btn.config(text=str(value), bg='#3498DB', fg='white',
                          state='normal', relief='raised',
                          activebackground='#2980B9')
        
        # Cập nhật stats
        current_state = PuzzleState(self.current_board)
        self.manhattan_label.config(text=str(current_state.heuristic))
        self.cost_label.config(text=str(current_state.cost))
        
        # Kiểm tra win condition
        if current_state.is_goal():
            self.status_var.set("🎉 Chúc mừng! Bạn đã giải thành công puzzle!")
            messagebox.showinfo("Thành công!", "🎉 Chúc mừng! Bạn đã hoàn thành puzzle!")
    
    def tile_clicked(self, row, col):
        """Xử lý khi click vào ô"""
        if self.is_solving:
            return
            
        clicked_index = row * 4 + col
        empty_index = self.current_board.index(0)
        empty_row, empty_col = empty_index // 4, empty_index % 4
        
        # Kiểm tra có thể di chuyển không
        if (abs(row - empty_row) == 1 and col == empty_col) or \
           (abs(col - empty_col) == 1 and row == empty_row):
            # Di chuyển ô
            self.current_board[clicked_index], self.current_board[empty_index] = \
                self.current_board[empty_index], self.current_board[clicked_index]
            
            # Hiệu ứng animation
            self.buttons[clicked_index].config(relief='sunken')
            self.root.after(100, lambda: self.update_display())
    
    def shuffle_puzzle(self):
        """Xáo trộn puzzle"""
        if self.is_solving:
            return
            
        # Tạo puzzle ngẫu nhiên bằng cách thực hiện các bước hợp lệ
        self.current_board = list(range(1, 16)) + [0]
        
        for _ in range(1000):
            empty_index = self.current_board.index(0)
            row, col = empty_index // 4, empty_index % 4
            
            moves = []
            if row > 0: moves.append(empty_index - 4)
            if row < 3: moves.append(empty_index + 4)
            if col > 0: moves.append(empty_index - 1)
            if col < 3: moves.append(empty_index + 1)
            
            new_index = random.choice(moves)
            self.current_board[empty_index], self.current_board[new_index] = \
                self.current_board[new_index], self.current_board[empty_index]
        
        self.update_display()
        self.clear_solution()
        self.status_var.set("Đã xáo trộn puzzle - Sẵn sàng giải!")
    
    def reset_puzzle(self):
        """Reset puzzle về trạng thái đích"""
        if self.is_solving:
            return
            
        self.current_board = list(range(1, 16)) + [0]
        self.update_display()
        self.clear_solution()
        self.status_var.set("Đã reset puzzle về trạng thái đích")
    
    def load_demo_puzzle(self):
        """Load puzzle demo khó"""
        if self.is_solving:
            return
            
        # Puzzle khó với Manhattan distance cao
        self.current_board = [5, 1, 3, 4, 2, 6, 8, 12, 9, 10, 7, 11, 13, 14, 0, 15]
        self.update_display()
        self.clear_solution()
        self.status_var.set("Đã load puzzle demo khó - Manhattan Distance cao!")
    
    def progress_callback(self, explored, frontier_size, heuristic, cost):
        """Callback để cập nhật tiến trình"""
        self.explored_label.config(text=f"{explored:,}")
        self.frontier_label.config(text=f"{frontier_size:,}")
        self.manhattan_label.config(text=str(heuristic))
        self.cost_label.config(text=str(cost))
        self.root.update()
    
    def solve_puzzle(self):
        """Giải puzzle bằng A*"""
        if self.is_solving:
            return
            
        if PuzzleState(self.current_board).is_goal():
            messagebox.showinfo("Thông báo", "Puzzle đã được giải rồi!")
            return
        
        # Kiểm tra tính khả giải
        if not self.solver.is_solvable(self.current_board):
            messagebox.showerror("Lỗi", "Puzzle này không thể giải được!\n\n" +
                               "Puzzle 15 chỉ có thể giải nếu số inversion phù hợp với vị trí ô trống.")
            return
        
        # Bắt đầu giải trong thread riêng
        self.is_solving = True
        self.solve_btn.config(state='disabled', text="🔄 Đang giải...")
        self.stop_btn.config(state='normal')
        self.progress_bar.pack(pady=10, fill='x')
        self.progress_bar.start()
        
        self.status_var.set("🤖 Đang chạy thuật toán A*... Vui lòng đợi")
        
        # Clear previous solution
        self.clear_solution()
        
        # Start solving in background thread
        def solve_thread():
            try:
                solution, stats = self.solver.solve(self.current_board, 
                                                  progress_callback=self.progress_callback,
                                                  stop_callback=lambda: not self.is_solving)
                
                # Update GUI trong main thread
                self.root.after(0, lambda: self.solve_completed(solution, stats))
                
            except Exception as e:
                self.root.after(0, lambda: self.solve_error(str(e)))
        
        threading.Thread(target=solve_thread, daemon=True).start()
    
    def solve_completed(self, solution, stats):
        """Hoàn thành giải puzzle"""
        self.is_solving = False
        self.solve_btn.config(state='normal', text="🤖 GIẢI BẰNG A* ALGORITHM")
        self.stop_btn.config(state='disabled')
        self.progress_bar.stop()
        self.progress_bar.pack_forget()
        
        if solution:
            # Cập nhật stats
            self.explored_label.config(text=f"{stats['explored']:,}")
            self.frontier_label.config(text=f"{stats['max_frontier']:,}")
            self.depth_label.config(text=str(stats['solution_length']))
            self.time_label.config(text=f"{stats['time']:.3f}s")
            
            # Hiển thị solution
            self.solution_path = solution
            self.display_solution()
            self.replay_btn.config(state='normal')
            
            self.status_var.set(f"✅ Tìm thấy lời giải trong {stats['solution_length']} bước! " +
                              f"Khám phá {stats['explored']:,} trạng thái.")
            
            messagebox.showinfo("Thành công!", 
                              f"🎉 Tìm thấy lời giải tối ưu!\n\n" +
                              f"📏 Số bước: {stats['solution_length']}\n" +
                              f"🔍 Trạng thái khám phá: {stats['explored']:,}\n" +
                              f"⏱️ Thời gian: {stats['time']:.3f}s")
        else:
            self.status_var.set("❌ Không tìm thấy lời giải trong thời gian cho phép")
            messagebox.showerror("Thất bại", "❌ Không thể tìm thấy lời giải!")
    
    def solve_error(self, error_msg):
        """Xử lý lỗi khi giải"""
        self.is_solving = False
        self.solve_btn.config(state='normal', text="🤖 GIẢI BẰNG A* ALGORITHM")
        self.stop_btn.config(state='disabled')
        self.progress_bar.stop()
        self.progress_bar.pack_forget()
        
        self.status_var.set(f"❌ Lỗi: {error_msg}")
        messagebox.showerror("Lỗi", f"❌ Có lỗi xảy ra: {error_msg}")
    
    def stop_solving(self):
        """Dừng quá trình giải"""
        self.is_solving = False
        self.solver.is_solving = False
        self.status_var.set("⏹️ Đã dừng quá trình giải")
    
    def display_solution(self):
        """Hiển thị lời giải"""
        self.solution_text.delete(1.0, tk.END)
        self.solution_text.insert(tk.END, "🎯 LỜI GIẢI TỪNG BƯỚC:\n")
        self.solution_text.insert(tk.END, "=" * 50 + "\n\n")
        
        for i, state in enumerate(self.solution_path):
            step_text = f"Bước {i}: {state.last_move if state.last_move else 'Trạng thái ban đầu'}\n"
            step_text += f"g(n)={state.moves}, h(n)={state.heuristic}, f(n)={state.cost}\n"
            
            # Hiển thị board
            for row in range(4):
                row_text = "│"
                for col in range(4):
                    val = state.board[row * 4 + col]
                    if val == 0:
                        row_text += "    │"
                    else:
                        row_text += f" {val:2d} │"
                step_text += row_text + "\n"
            
            step_text += "\n" + "-" * 30 + "\n\n"
            self.solution_text.insert(tk.END, step_text)
    
    def clear_solution(self):
        """Xóa lời giải"""
        self.solution_text.delete(1.0, tk.END)
        self.solution_path = []
        self.replay_btn.config(state='disabled')
        
        # Reset stats
        self.explored_label.config(text="0")
        self.frontier_label.config(text="0")
        self.depth_label.config(text="0")
        self.time_label.config(text="0ms")
    
    def start_replay(self):
        """Bắt đầu replay animation"""
        if not self.solution_path:
            return
            
        self.replay_index = 0
        self.replay_btn.config(state='disabled', text="🎬 Đang replay...")
        self.replay_step()
    
    def replay_step(self):
        """Thực hiện một bước replay"""
        if self.replay_index >= len(self.solution_path):
            self.replay_btn.config(state='normal', text="🎬 Replay")
            self.status_var.set("🎬 Hoàn thành replay animation")
            return
        
        # Cập nhật board
        state = self.solution_path[self.replay_index]
        self.current_board = state.board[:]
        self.update_display()
        
        # Cập nhật status
        step_info = f"Replay bước {self.replay_index}: {state.last_move if state.last_move else 'Ban đầu'}"
        self.status_var.set(step_info)
        
        # Highlight step trong solution text
        self.highlight_current_step()
        
        self.replay_index += 1
        self.root.after(1000, self.replay_step)  # Delay 1 giây
    
    def highlight_current_step(self):
        """Highlight bước hiện tại trong solution text"""
        self.solution_text.tag_remove('highlight', 1.0, tk.END)
        
        # Tìm và highlight bước hiện tại
        content = self.solution_text.get(1.0, tk.END)
        step_marker = f"Bước {self.replay_index}:"
        
        start_pos = content.find(step_marker)
        if start_pos != -1:
            start_index = f"1.{start_pos}"
            end_pos = content.find(f"Bước {self.replay_index + 1}:", start_pos)
            if end_pos == -1:
                end_index = tk.END
            else:
                end_index = f"1.{end_pos}"
            
            self.solution_text.tag_add('highlight', start_index, end_index)
            self.solution_text.tag_config('highlight', background='#3498DB', foreground='white')
            self.solution_text.see(start_index)
    
    def create_custom_puzzle(self):
        """Tạo cửa sổ nhập puzzle tùy chỉnh"""
        if self.is_solving:
            return
            
        custom_window = tk.Toplevel(self.root)
        custom_window.title("Nhập Puzzle Tùy chỉnh")
        custom_window.geometry("400x300")
        custom_window.configure(bg='#2C3E50')
        custom_window.transient(self.root)
        custom_window.grab_set()
        
        # Center window
        custom_window.update_idletasks()
        x = (custom_window.winfo_screenwidth() // 2) - (400 // 2)
        y = (custom_window.winfo_screenheight() // 2) - (300 // 2)
        custom_window.geometry(f"+{x}+{y}")
        
        tk.Label(custom_window, text="Nhập 16 số từ 0-15 (0 là ô trống)",
                font=('Arial', 12, 'bold'), fg='#ECF0F1', bg='#2C3E50').pack(pady=20)
        
        tk.Label(custom_window, text="Ví dụ: 1 2 3 4 5 6 7 8 9 10 11 12 13 14 0 15",
                font=('Arial', 10), fg='#BDC3C7', bg='#2C3E50').pack(pady=5)
        
        entry_var = tk.StringVar()
        entry = tk.Entry(custom_window, textvariable=entry_var, width=50, 
                        font=('Arial', 12), justify='center')
        entry.pack(pady=20)
        entry.focus()
        
        def apply_custom():
            try:
                numbers = list(map(int, entry_var.get().split()))
                if len(numbers) != 16 or set(numbers) != set(range(16)):
                    messagebox.showerror("Lỗi", "Phải nhập đúng 16 số từ 0-15!")
                    return
                
                self.current_board = numbers
                self.update_display()
                self.clear_solution()
                custom_window.destroy()
                self.status_var.set("Đã áp dụng puzzle tùy chỉnh")
                
            except ValueError:
                messagebox.showerror("Lỗi", "Vui lòng nhập số hợp lệ!")
        
        button_frame = tk.Frame(custom_window, bg='#2C3E50')
        button_frame.pack(pady=20)
        
        tk.Button(button_frame, text="✅ Áp dụng", command=apply_custom,
                 bg='#27AE60', fg='white', font=('Arial', 10, 'bold'),
                 padx=20, pady=5).pack(side='left', padx=10)
        
        tk.Button(button_frame, text="❌ Hủy", command=custom_window.destroy,
                 bg='#E74C3C', fg='white', font=('Arial', 10, 'bold'),
                 padx=20, pady=5).pack(side='left', padx=10)
        
        # Bind Enter key
        entry.bind('<Return>', lambda e: apply_custom())
    
    def show_algorithm_details(self):
        """Hiển thị chi tiết thuật toán A*"""
        details_window = tk.Toplevel(self.root)
        details_window.title("Chi tiết Thuật toán A*")
        details_window.geometry("600x500")
        details_window.configure(bg='#2C3E50')
        details_window.transient(self.root)
        
        # Center window
        details_window.update_idletasks()
        x = (details_window.winfo_screenwidth() // 2) - (600 // 2)
        y = (details_window.winfo_screenheight() // 2) - (500 // 2)
        details_window.geometry(f"+{x}+{y}")
        
        text_widget = scrolledtext.ScrolledText(details_window, font=('Arial', 11),
                                              bg='#34495E', fg='#ECF0F1',
                                              insertbackground='#ECF0F1')
        text_widget.pack(expand=True, fill='both', padx=20, pady=20)
        
        algorithm_text = """🧠 THUẬT TOÁN A* (A-STAR SEARCH)

📖 GIỚI THIỆU:
A* là thuật toán tìm kiếm có thông tin (informed search) được sử dụng rộng rãi 
trong trí tuệ nhân tạo để tìm đường đi tối ưu từ trạng thái ban đầu đến đích.

🔬 CÔNG THỨC ĐÁNH GIÁ:
f(n) = g(n) + h(n)

Trong đó:
• g(n): Chi phí thực tế từ trạng thái ban đầu đến trạng thái n
• h(n): Heuristic - ước tính chi phí từ n đến trạng thái đích
• f(n): Tổng ước tính chi phí của đường đi qua n

🎯 HEURISTIC - MANHATTAN DISTANCE:
Với puzzle 15, chúng ta sử dụng Manhattan Distance làm heuristic:
• Tính tổng khoảng cách theo trục x và y của mỗi ô đến vị trí đích
• Công thức: |x1-x2| + |y1-y2| cho mỗi ô
• Đây là heuristic "admissible" - không bao giờ overestimate chi phí thực tế

⚙️ CÁCH HOẠT ĐỘNG:
1. Bắt đầu với trạng thái ban đầu trong frontier (priority queue)
2. Lặp lại cho đến khi tìm thấy đích:
   - Chọn trạng thái có f(n) nhỏ nhất từ frontier
   - Nếu là đích → hoàn thành
   - Nếu không → mở rộng trạng thái này
   - Thêm các trạng thái kế tiếp vào frontier
   - Đánh dấu trạng thái hiện tại đã khám phá

🎮 ĐẶC ĐIỂM PUZZLE 15:
• Không phải puzzle nào cũng có thể giải được
• Chỉ 50% các cấu hình ngẫu nhiên có thể giải
• Kiểm tra bằng "inversion count" và vị trí ô trống

📈 ĐỘ PHỨC TẠP:
• Time Complexity: O(b^d) trong trường hợp xấu nhất
• Space Complexity: O(b^d)
• Với puzzle khó có thể cần khám phá hàng chục nghìn trạng thái

🏆 ƯU ĐIỂM A*:
• Đảm bảo tìm được lời giải tối ưu (nếu heuristic admissible)
• Hiệu quả hơn các thuật toán tìm kiếm mù (blind search)
• Có thể điều chỉnh heuristic để cân bằng tốc độ và tối ưu

💡 HEURISTIC KHÁC CÓ THỂ SỬ DỤNG:
• Linear Conflict: Phát hiện xung đột trong cùng hàng/cột
• Pattern Database: Lưu trữ chi phí tối ưu cho các mẫu con
• Walking Distance: Kết hợp Manhattan với walking distance"""

        text_widget.insert(tk.END, algorithm_text)
        text_widget.config(state='disabled')
    
    def run(self):
        """Chạy ứng dụng"""
        # Thêm menu bar
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)
        
        # File menu
        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="📁 File", menu=file_menu)
        file_menu.add_command(label="🎲 Puzzle ngẫu nhiên", command=self.shuffle_puzzle)
        file_menu.add_command(label="✏️ Nhập tùy chỉnh", command=self.create_custom_puzzle)
        file_menu.add_command(label="📚 Puzzle demo", command=self.load_demo_puzzle)
        file_menu.add_separator()
        file_menu.add_command(label="❌ Thoát", command=self.root.quit)
        
        # Help menu
        help_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="❓ Trợ giúp", menu=help_menu)
        help_menu.add_command(label="🧠 Chi tiết thuật toán A*", command=self.show_algorithm_details)
        help_menu.add_command(label="ℹ️ Hướng dẫn", command=self.show_instructions)
        
        # Bắt đầu với puzzle xáo trộn
        self.shuffle_puzzle()
        
        # Chạy main loop
        self.root.mainloop()
    
    def show_instructions(self):
        """Hiển thị hướng dẫn sử dụng"""
        instructions_window = tk.Toplevel(self.root)
        instructions_window.title("Hướng dẫn sử dụng")
        instructions_window.geometry("500x400")
        instructions_window.configure(bg='#2C3E50')
        instructions_window.transient(self.root)
        
        # Center window
        instructions_window.update_idletasks()
        x = (instructions_window.winfo_screenwidth() // 2) - (500 // 2)
        y = (instructions_window.winfo_screenheight() // 2) - (400 // 2)
        instructions_window.geometry(f"+{x}+{y}")
        
        text_widget = scrolledtext.ScrolledText(instructions_window, font=('Arial', 11),
                                              bg='#34495E', fg='#ECF0F1',
                                              insertbackground='#ECF0F1')
        text_widget.pack(expand=True, fill='both', padx=20, pady=20)
        
        instructions_text = """🎮 HƯỚNG DẪN SỬ DỤNG 15-PUZZLE SOLVER

🎯 MỤC TIÊU:
Sắp xếp các số từ 1-15 theo thứ tự tăng dần, với ô trống ở cuối.

🎲 BẮT ĐẦU:
1. Nhấn "Xáo trộn" để tạo puzzle ngẫu nhiên
2. Hoặc chọn "Demo" để thử puzzle mẫu khó
3. Hoặc nhập puzzle tùy chỉnh qua menu File

🎮 CHƠI THỦ CÔNG:
• Click vào các ô số cạnh ô trống để di chuyển
• Chỉ có thể di chuyển ô kề với ô trống

🤖 GIẢI TỰ ĐỘNG:
• Nhấn "GIẢI BẰNG A* ALGORITHM" để AI giải
• Theo dõi thống kê thuật toán realtime
• Xem lời giải từng bước sau khi hoàn thành

🎬 TÍNH NĂNG REPLAY:
• Xem animation từng bước của lời giải
• Theo dõi cách AI di chuyển từng ô

📊 THỐNG KÊ THUẬT TOÁN:
• Trạng thái khám phá: Số state AI đã xem xét
• Frontier tối đa: Kích thước queue lớn nhất
• Độ sâu giải pháp: Số bước tối ưu
• Manhattan Distance: Giá trị heuristic hiện tại
• Chi phí f(n): Tổng g(n) + h(n)

💡 MẸO:
• Không phải puzzle nào cũng giải được (chỉ ~50%)
• Puzzle khó có thể mất vài phút để giải
• Manhattan Distance càng thấp càng gần đích
• A* đảm bảo tìm lời giải tối ưu (ít bước nhất)

🔬 VỀ THUẬT TOÁN A*:
• Tìm kiếm có thông tin (informed search)
• Sử dụng heuristic để định hướng tìm kiếm
• Kết hợp ưu điểm của Dijkstra và Greedy Search
• Được dùng rộng rãi trong AI, robotics, game development"""

        text_widget.insert(tk.END, instructions_text)
        text_widget.config(state='disabled')

def create_random_solvable_puzzle() -> List[int]:
    """Tạo puzzle ngẫu nhiên có thể giải được"""
    puzzle = list(range(16))
    
    # Xáo trộn bằng cách thực hiện các bước di chuyển hợp lệ
    for _ in range(1000):
        empty_pos = puzzle.index(0)
        row, col = empty_pos // 4, empty_pos % 4
        
        moves = []
        if row > 0: moves.append(empty_pos - 4)
        if row < 3: moves.append(empty_pos + 4)
        if col > 0: moves.append(empty_pos - 1)
        if col < 3: moves.append(empty_pos + 1)
        
        new_pos = random.choice(moves)
        puzzle[empty_pos], puzzle[new_pos] = puzzle[new_pos], puzzle[empty_pos]
    
    return puzzle

def main():
    """Hàm main khởi chạy ứng dụng"""
    print("🚀 Khởi động 15-Puzzle Solver GUI...")
    print("🧠 Thuật toán: A* Search với Manhattan Distance Heuristic")
    print("🎯 Mục tiêu: Tìm lời giải tối ưu cho bài toán 15-puzzle")
    print("-" * 60)
    
    try:
        app = PuzzleGUI()
        app.run()
    except KeyboardInterrupt:
        print("\n👋 Ứng dụng đã được dừng bởi người dùng")
    except Exception as e:
        print(f"❌ Lỗi: {e}")

if __name__ == "__main__":
    main()

"""
🎨 THIẾT KẾ GIAO DIỆN ĐẶC ĐIỂM:

1. 🖼️ LAYOUT CHÍNH:
   - Header với tiêu đề gradient animation
   - Panel trái: Bảng puzzle với controls
   - Panel phải: Thống kê và lời giải
   - Menu bar với các tính năng mở rộng

2. 🎮 PUZZLE BOARD:
   - Grid 4x4 với animation khi click
   - Màu sắc gradient cho các ô số
   - Hover effects và transitions mượt mà
   - Ô trống có styling riêng biệt

3. 📊 THỐNG KÊ REAL-TIME:
   - Cập nhật liên tục khi thuật toán chạy
   - Hiển thị các metrics quan trọng
   - Color coding cho từng loại thông tin
   - Progress bar khi đang giải

4. 🎯 PANEL LỜI GIẢI:
   - ScrolledText để hiển thị từng bước
   - Syntax highlighting cho các bước
   - Replay animation với highlight
   - Export solution option

5. 🎨 VISUAL EFFECTS:
   - Gradient backgrounds và animations
   - Hover effects trên tất cả buttons
   - Smooth transitions khi di chuyển ô
   - Color-coded statistics

6. 📱 RESPONSIVE DESIGN:
   - Tự động điều chỉnh theo kích thước màn hình
   - Mobile-friendly controls
   - Scalable font sizes

7. 🔧 TÍNH NĂNG NÂNG CAO:
   - Custom puzzle input dialog
   - Algorithm explanation window
   - Menu system với shortcuts
   - Threading để không block UI
   - Progress tracking với callbacks

CÁCH CHẠY:
python puzzle_gui.py

Giao diện sẽ khởi động với puzzle đã xáo trộn sẵn sàng để giải!
"""