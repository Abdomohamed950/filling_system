def validate_password(input_password, correct_password):
    return input_password == correct_password

def add_operator(operators_list, new_operator):
    if new_operator not in operators_list:
        operators_list.append(new_operator)
        return True
    return False

def remove_operator(operators_list, operator_to_remove):
    if operator_to_remove in operators_list:
        operators_list.remove(operator_to_remove)
        return True
    return False

def list_operators(operators_list):
    return operators_list.copy()