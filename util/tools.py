def change_win_path_to_linux(win_path):
    return '/'.join(win_path.split('\\'))


def change_lin_path_to_win(lin_path):
    return '\\'.join(lin_path.split('/'))