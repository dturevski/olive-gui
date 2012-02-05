import common, chess

def check(problem, board, solution):
    retval = common.retval(provides)
    
    for twin in solution.siblings:
        if not twin.stipulation.style in ['', 's', 'r']:
            continue
        twin.make(board)
        keyplay = twin.keyplay()
        fb = get_flights(board) # flights before key
        for key in keyplay.siblings:
            # check
            if key.move.is_check:
                retval['Checking key'] = True
            # withdrawal
            if twin.stipulation.style == '' and key.move.dep[0] <> 'P':
                (kx, ky) = chess.LookupTables.to_xy(board.kings[chess.BLACK])
                (bx, by) = chess.LookupTables.to_xy(key.move.dep[1])
                (ax, ay) = chess.LookupTables.to_xy(key.move.arr[1])
                distance_diff = ((ax-kx)**2 + (ay-ky)**2) - ((bx-kx)**2 + (by-ky)**2) 
                retval['Withdrawal key'] |= distance_diff > 3
            # flights
            key.make(board)
            fa = get_flights(board) # flights after key
            key.unmake(board)
            
            diff = fa.count_set_bits() - fb.count_set_bits() 
            
            retval['Flight giving key'] |= diff > 0
            retval['Flight giving key(2)'] |= diff > 1
            retval['Flight giving key(3)'] |= diff > 2
            retval['Flight giving key(4)'] |= diff > 3
            retval['Flight giving key(5)'] |= diff > 4
            retval['Flight giving key(6+)'] |= diff > 5

            retval['Flight taking key'] |= diff < 0
            retval['Flight taking key(2)'] |= diff < -1
            retval['Flight taking key(3)'] |= diff < -2
            retval['Flight taking key(4)'] |= diff < -3
            retval['Flight taking key(5)'] |= diff < -4
            retval['Flight taking key(6)'] |= diff < -5

            retval['Flight giving and taking key'] |= (not ((fb ^ fa) & fa).is_zero()) and \
                                        (not ((fb ^ fa) & fb).is_zero())
        twin.unmake(board)

    return retval

# returns the BitBoard with black king flight squares 
def get_flights(board):
    retval = chess.BitBoard()
    for move in chess.LegalMoves(board, chess.BLACK):
        if(move.dep[0] == 'k'):
            retval[move.arr[1]] = 1
    return retval