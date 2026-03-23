#!/usr/bin/env python3
"""
国际象棋自动对弈 - cliclick 坐标版
白方(我) vs 电脑黑方
"""
import subprocess, time, re, os

PIECE_MAP = {
    '白车': 'R', '白马': 'N', '白象': 'B', '白后': 'Q', '白王': 'K', '白兵': 'P',
    '黑车': 'r', '黑马': 'n', '黑象': 'b', '黑后': 'q', '黑王': 'k', '黑兵': 'p',
}

# 棋盘在屏幕上的位置（从 group 1 获取）
BOARD_ORIGIN_X = 139
BOARD_ORIGIN_Y = 127
BOARD_WIDTH    = 923
BOARD_HEIGHT   = 691
SQ_W = BOARD_WIDTH  / 8.0   # ~115.4 px
SQ_H = BOARD_HEIGHT / 8.0   # ~86.4 px

def sq_to_screen(col, rank):
    """将棋谱坐标(col 0-7, rank 1-8)转为屏幕中心坐标"""
    cx = BOARD_ORIGIN_X + (col + 0.5) * SQ_W
    row = 8 - rank
    cy = BOARD_ORIGIN_Y + (row + 0.5) * SQ_H
    return int(cx), int(cy)

def cliclick_at(sq):
    """用 cliclick 点击棋谱格子"""
    col = ord(sq[0]) - ord('a')
    rank = int(sq[1])
    cx, cy = sq_to_screen(col, rank)
    os.system(f'cliclick t:{cx},{cy}')
    return cx, cy

def run(code):
    r = subprocess.run(['osascript', '-e', code], capture_output=True, text=True)
    out = r.stdout.strip()
    return out if out not in ('', 'missing value') else None

def get_board_desc():
    return run('''tell application "System Events" to tell process "Chess"
        set frontmost to true
        tell window 1
            get description of buttons of group 1
        end tell
    end tell''')

def get_window_title():
    out = run('''tell application "System Events" to tell process "Chess"
        set frontmost to true
        get name of window 1
    end tell''')
    return out or ''

def get_turn():
    return '白方走棋' in get_window_title()

def is_game_over(state):
    if not state: return None
    if '白胜' in state or '白方胜' in state: return 'WHITE_WINS'
    if '黑胜' in state or '黑方胜' in state: return 'BLACK_WINS'
    if '平' in state or '和棋' in state: return 'DRAW'
    return None

def find_piece(state, square):
    m = re.search(r'(白车|白马|白象|白后|白王|白兵|黑马|黑象|黑后|黑王|黑兵|黑车)[,\s]+' + square, state)
    return m.group(1) if m else None

def do_move(from_sq, to_sq, state):
    """坐标点击方式执行走棋"""
    piece = find_piece(state, from_sq)
    if not piece:
        return False
    
    # 点击起始格
    c1 = cliclick_at(from_sq)
    print(f"    ♟ {piece} {from_sq} → {to_sq}  (点击 {c1[0]},{c1[1]})")
    time.sleep(0.4)
    
    # 点击目标格
    c2 = cliclick_at(to_sq)
    print(f"    ↳ 落子 {c2[0]},{c2[1]}")
    time.sleep(0.8)
    return True

def parse_board(state):
    board = {}
    for f in 'abcdefgh':
        for r in '12345678':
            sq = f + r
            p = find_piece(state, sq)
            board[sq] = PIECE_MAP.get(p, '') if p else ''
    return board

def board_to_fen(board, is_white):
    rows = []
    for rank in '87654321':
        row, empty = '', 0
        for file in 'abcdefgh':
            p = board.get(file + rank, '')
            if p:
                if empty: row += str(empty); empty = 0
                row += p
            else:
                empty += 1
        if empty: row += str(empty)
        rows.append(row)
    fen = '/'.join(rows) + ' ' + ('w' if is_white else 'b') + ' KQkq - 0 1'
    return fen

def best_move(fen):
    cmd = f"position fen {fen}\nsetoption name MultiPV value 1\ngo depth 20\nquit\n"
    try:
        r = subprocess.run(['stockfish'], input=cmd,
                          capture_output=True, text=True, timeout=15)
        for line in r.stdout.split('\n'):
            if line.startswith('bestmove'):
                return line.split()[1]
    except:
        pass
    return None

def wait_for_turn_change(initial_is_white, timeout=40):
    for _ in range(timeout):
        time.sleep(1.5)
        state = get_board_desc()
        over = is_game_over(state)
        if over:
            return state, over
        now_white = get_turn()
        if now_white != initial_is_white:
            return state, False
    return get_board_desc(), True

def print_board(board):
    print("    a b c d e f g h")
    for rank in '87654321':
        row = f"  {rank} "
        for file in 'abcdefgh':
            p = board.get(file + rank, '')
            row += (p if p else '.') + ' '
        print(row)

def main():
    print("=" * 47)
    print("  ♟  国际象棋自动对弈  |  白方(我) vs 电脑(黑方) ♟")
    print("=" * 47)

    moves = []
    rnd = 1

    while True:
        state = get_board_desc()
        if not state:
            print("⚠ 读取棋盘失败，等待...")
            time.sleep(2)
            continue

        over = is_game_over(state)
        if over:
            print(f"\n{'='*47}")
            names = {
                'WHITE_WINS': '🏆 白方胜利！战胜电脑！',
                'BLACK_WINS': '😢 黑方胜利（电脑赢了）',
                'DRAW': '🤝 平局！'
            }
            print(f"  {names.get(over, over)}")
            print(f"  总步数: {len(moves)}")
            if moves:
                print(f"  走法: {' '.join(moves)}")
            print("=" * 47)
            break

        is_white = get_turn()
        board = parse_board(state)
        fen = board_to_fen(board, is_white)

        print(f"\n━━ 第 {rnd} 回合 ━━ {'白方(我) ♔' if is_white else '黑方(电脑) ♚'}")
        print_board(board)

        if not is_white:
            # 轮到电脑，读取即可
            print("  ⏳ 等待电脑走棋...")
            _, result = wait_for_turn_change(is_white)
            if result not in (False, None):
                state = get_board_desc()
                over = is_game_over(state)
                if over:
                    print(f"\n{'='*47}")
                    print(f"  {'🏆' if over=='WHITE_WINS' else '😢' if over=='BLACK_WINS' else '🤝'} {names.get(over, over)}")
                    print("=" * 47)
                    break
            rnd += 1
            continue

        mv = best_move(fen)
        if not mv:
            print("  ❌ Stockfish 无走法，等待...")
            time.sleep(2)
            continue

        print(f"  🤖 Stockfish: {mv}")

        if len(mv) < 4:
            continue

        from_sq, to_sq = mv[:2], mv[2:4]
        promo = mv[4] if len(mv) > 4 else None

        if not do_move(from_sq, to_sq, state):
            print(f"  ❌ 无法执行 {from_sq} → {to_sq}，等待...")
            time.sleep(1)
            continue

        # 升变处理
        if promo:
            time.sleep(0.5)
            promo_sq = to_sq  # 升变格就是目标格
            promo_map = {'q': 'Q', 'r': 'R', 'b': 'B', 'n': 'N'}
            print(f"  ♕ 升变为 {promo_map.get(promo, 'Q')}！")
            # 在目标格再次点击确认升变选择

        moves.append(mv)
        print(f"  ✅ 已走: {mv}")

        # 等待电脑回应
        print(f"  ⏳ 等待电脑回应...")
        new_state, result = wait_for_turn_change(is_white)
        if result == True:
            print("  ⚠ 等待超时，重新读取")
        elif result not in (False, None):
            state = result
            over = is_game_over(state)
            if over:
                print(f"\n{'='*47}")
                print(f"  🏆/😢/🤝 {over}")
                print("=" * 47)
                break

        rnd += 1

if __name__ == '__main__':
    main()
