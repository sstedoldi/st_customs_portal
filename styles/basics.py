def hide(class_id):
    return '''<style>
    %(class_id)s 
    {
        visibility: hidden;    
    }
    </style>''' % {"class_id": class_id}

def lg_color(class_id):
    return '''<style>
    %(class_id)s
    {
        background-image: linear-gradient(90deg, rgb(88, 110, 118), rgb(173, 216, 230));   
    }
    </style>''' % {"class_id": class_id}

def cont_padding(class_id):
    return '''<style>
    %(class_id)s
    {
        padding: 16px;
    }
    </style>''' % {"class_id": class_id}