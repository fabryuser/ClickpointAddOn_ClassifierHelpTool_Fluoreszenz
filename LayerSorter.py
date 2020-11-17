from __future__ import division,print_function
import clickpoints
import glob
import peewee
import os
import numpy as np

from NameGlob import nameGlob, getValue, nameGlobFiles



#TODO change path
path_list = nameGlob(r'F:\Versuche\Trainingsdaten\2020-10-06_Immunecells_Hoechst\data\15sec')


def Create_DB(database_name, pic_path, pic_pos, add_fl_max_projection=False):

    try:
        db = clickpoints.DataFile(database_name, 'w')
    except peewee.OperationalError:
        print(database_name)
        raise

    # Workaround base layer issue
    layers = ["MinProj", "MinIndices", "MaxProj", "MaxIndices"]

    base = db.getLayer(layers[0], create=True)
    for l in layers[1:]:
        db.getLayer(l, base_layer=base, create=True)

    # get all images in the folder that match the path
    images = glob.glob(pic_path)
    # iterate over all images
    repetitions_sort_index = {}
    sort_index = 0

    for image_path in images:
        image_filename = os.path.basename(image_path)
        layer = [l for l in layers if l in image_path]
        if len(layer) != 1:
            raise ValueError("No known layer!")
        rep = getValue(image_filename, "*_rep{rep}_pos*")["rep"]
        image = db.setImage(filename=image_path, layer=layer[0])

        #if first image was deleted: image.sort_index = int(rep)-1
        if rep not in repetitions_sort_index:
            repetitions_sort_index[rep] = sort_index
            sort_index += 1
        image.sort_index = repetitions_sort_index[rep]
        image.save()

    if add_fl_max_projection:

        db.getLayer("Fluo", base_layer=base, create=True)
        images = glob.glob(pic_path.replace("POL","Fluo"))
        for image_path in images:
            image_filename = os.path.basename(image_path)
            if "zMaxProj" in image_path:
                rep = getValue(image_filename, "*_rep{rep}_pos*")["rep"]
                image = db.setImage(filename=image_path, layer="Fluo")

                # if first image was deleted: image.sort_index = int(rep)-1
                if rep not in repetitions_sort_index:
                    repetitions_sort_index[rep] = sort_index
                    sort_index += 1
                image.sort_index = repetitions_sort_index[rep]
                image.save()

    db.db.close()



for path, extra in path_list:
    #check if config data exists
    measurements = glob.glob(os.path.join(path, "*_Config.txt"))
    # create config data if not available
    if len(measurements) == 0:
        image_filenames = nameGlobFiles(os.path.join(path, "*.tif"))
        for img in image_filenames:
            head, tail = os.path.split(img[0])
            config = tail[:16]
            configname = os.path.join(path, config + 'Config' + r".txt")
            file = open(configname, "w")
            file.close()
            continue

    measurements = glob.glob(os.path.join(path, "*_Config.txt"))

    if len(measurements) == 0:
        continue

    measurement = sorted(measurements)[-1]

    measurement = sorted(measurements)[-1]
    # split the date string from the name e.g. "20180205-103213"
    measurement_date_id = os.path.basename(measurement)[:15]

    # get all image filenames for that measurement
    image_filenames = nameGlobFiles(os.path.join(path, measurement_date_id+"*_pos{pos}_*POL*.tif"))

    # extract all unique position identifiers e.g. 000, 001, ...
    positions = np.unique([extra["pos"] for filename, extra in image_filenames])

    for pos in positions:
        pos = "pos"+pos
        Fin_Name = os.path.join(path, measurement_date_id+"_"+pos+ "POL" + ".cdb")
        pic_path = os.path.join(path, measurement_date_id+'*_'+pos+"*POL*.tif")
        print(Fin_Name)
        print(pic_path)
        print(pos)
        Create_DB(Fin_Name, pic_path, pos, add_fl_max_projection=True)




print("-----Done-----")