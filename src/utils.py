def geo_mean(imprv_list):
    result = 1
    for i in imprv_list:
        result *= i
    return result ** (1/len(imprv_list))