def recycling_yield(input_kg:float, output_kg:float)->float:
    if input_kg <= 0: raise ValueError("input_kg must be positive")
    if output_kg < 0 or output_kg > input_kg: raise ValueError("output_kg must be between zero and input_kg")
    return round(output_kg/input_kg*100,2)
