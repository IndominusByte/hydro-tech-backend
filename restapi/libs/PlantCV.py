import os, cv2
from plantcv import plantcv as pcv

class PlantCV:
    base_dir: str = os.path.join(os.path.dirname(__file__),'../static/')

    @classmethod
    def measure_plants(cls, image: str, user_id: str, debug: str = None) -> float:
        path_in = os.path.join(cls.base_dir,'camera_module',user_id)
        path_out = os.path.join(cls.base_dir,'camera_module_output',user_id)
        # make directory if not exists
        if not os.path.exists(path_out):
            os.mkdir(path_out)

        pcv.params.debug = debug  # set debug mode
        pcv.params.debug_outdir = os.path.join(path_out,image)  # set output directory

        # Read image
        img, path, filename = pcv.readimage(filename=os.path.join(path_in,image), mode="rgb")

        # Create binary image of edges.
        edges = pcv.canny_edge_detect(img)

        # Apply Mask (for VIS images, mask_color=white)
        masked = pcv.apply_mask(img=img, mask=edges, mask_color='white')

        # Identify objects
        id_objects, obj_hierarchy = pcv.find_objects(masked, edges)

        # Define ROI
        roi1, roi_hierarchy = pcv.roi.rectangle(img=masked, x=0, y=0, w=640, h=480)

        # Decide which objects to keep
        roi_objects, hierarchy3, kept_mask, obj_area = pcv.roi_objects(
            img=img, roi_contour=roi1,
            roi_hierarchy=roi_hierarchy,
            object_contour=id_objects,
            obj_hierarchy=obj_hierarchy,
            roi_type='partial'
        )

        # Object combine kept objects
        obj, mask = pcv.object_composition(img=img, contours=roi_objects, hierarchy=hierarchy3)

        # Shape properties relative to user boundary line (optional)
        boundary_img1 = pcv.analyze_bound_horizontal(img=img, obj=obj, mask=mask, line_position=355, label="boundary")

        # get height plant in cm
        output_boundary = pcv.outputs.observations['boundary']
        height_above = output_boundary['height_above_reference']['value']
        height_below = output_boundary['height_below_reference']['value']
        cmPerPixel = 0.155

        plantHeight = abs((height_above - height_below) * cmPerPixel)

        cv2.putText(boundary_img1,"{:.1f}cm".format(plantHeight),(50,50),cv2.FONT_HERSHEY_SIMPLEX,0.8,(255, 255, 255),2)
        cv2.imwrite(os.path.join(path_out,image),boundary_img1)

        return plantHeight
