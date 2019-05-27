################################################################################
#                             PROYECTO # 2 GRAFICAS                            #
################################################################################
#Nombre: Esteban Cabrera Arevalo.
#Carnet: 17781.
#Fecha: 07/05/2019.

#*Codigo inspirado en el de Ing. Dennis Aldana.*

import pygame #Libreria del GUI.
from OpenGL.GL import * #Libreria OpenGL
from OpenGL.GL.shaders import compileProgram, compileShader
import glm #Libreria matrices.
import pyassimp
import numpy
import math #Libreria para operaciones matematicas.

################################################################################
#                             SET-UP DE PYGAME                                 #
################################################################################
screen = pygame.display.set_mode((800, 600), pygame.OPENGL | pygame.DOUBLEBUF)

clock = pygame.time.Clock()

glClearColor(1.0, 1.0, 1.0, 1.0)
glEnable(GL_DEPTH_TEST)
glEnable(GL_TEXTURE_2D)
################################################################################

################################################################################
#                             SET-UP DE SHADERS                                #
################################################################################
vertex_shader = """
#version 460
layout (location = 0) in vec4 position;
layout (location = 1) in vec4 normal;
layout (location = 2) in vec2 texcoords;

//Se reserva el espacio de las matrices
uniform mat4 model;
uniform mat4 view;
uniform mat4 projection;

uniform vec4 color;
uniform vec4 light;

out vec4 vertexColor;
out vec2 vertexTexcoords;

void main()
{
    float intensity = dot(normal, normalize(light - position));
    gl_Position = projection * view * model * position;
    vertexColor = color * intensity;
    vertexTexcoords = texcoords;
}

"""

fragment_shader = """
#version 460
layout (location = 0) out vec4 diffuseColor;

in vec4 vertexColor;
in vec2 vertexTexcoords;

uniform sampler2D tex;

void main()
{
    diffuseColor = vertexColor * texture(tex, vertexTexcoords);
}
"""

shader = compileProgram(
    compileShader(vertex_shader, GL_VERTEX_SHADER),
    compileShader(fragment_shader, GL_FRAGMENT_SHADER),
)

glUseProgram(shader)
################################################################################

################################################################################
#                             SET-UP DE MATRICES                               #
################################################################################
model = glm.mat4(1)
view = glm.mat4(1)
projection = glm.perspective(glm.radians(45), 800/600, 0.1, 1000.0)

glViewport(0, 0, 800, 600)
################################################################################

scene = pyassimp.load('./Obj/CastleOBJ.obj') #Carga del castillo (OBJ)

def glize(node, light, recTexture, difuse):
    
    model = node.transformation.astype(numpy.float32)

    for mesh in node.meshes:
        material = dict(mesh.material.properties.items())
        texture = material['file']
        
        if recTexture == False:
            texture_surface = pygame.image.load("./Obj/" + texture)
            texture_data = pygame.image.tostring(texture_surface,"RGB",1)
            width = texture_surface.get_width()
            height = texture_surface.get_height()
            texture = glGenTextures(1)
            glBindTexture(GL_TEXTURE_2D, texture)
            glTexImage2D(GL_TEXTURE_2D, 0, GL_RGB, width, height, 0, GL_RGB, GL_UNSIGNED_BYTE, texture_data)
            glGenerateMipmap(GL_TEXTURE_2D)
        else:
            texture_surface = pygame.image.load("./Obj/CastleExterior TextureBump.jpg" )
            texture_data = pygame.image.tostring(texture_surface,"RGB",1)
            width = texture_surface.get_width()
            height = texture_surface.get_height()
            texture = glGenTextures(1)
            glBindTexture(GL_TEXTURE_2D, texture)
            glTexImage2D(GL_TEXTURE_2D, 0, GL_RGB, width, height, 0, GL_RGB, GL_UNSIGNED_BYTE, texture_data)
            glGenerateMipmap(GL_TEXTURE_2D)
            
        vertex_data = numpy.hstack((
            numpy.array(mesh.vertices, dtype=numpy.float32),
            numpy.array(mesh.normals, dtype=numpy.float32),
            numpy.array(mesh.texturecoords[0], dtype=numpy.float32)
        ))

        faces = numpy.hstack(
            numpy.array(mesh.faces, dtype=numpy.int32)
        )

        vertex_buffer_object = glGenVertexArrays(1)
        glBindBuffer(GL_ARRAY_BUFFER, vertex_buffer_object)
        glBufferData(GL_ARRAY_BUFFER, vertex_data.nbytes, vertex_data, GL_STATIC_DRAW)

        glVertexAttribPointer(0, 3, GL_FLOAT, False, 9 * 4, None)
        glEnableVertexAttribArray(0)
        glVertexAttribPointer(1, 3, GL_FLOAT, False, 9 * 4, ctypes.c_void_p(3 * 4))
        glEnableVertexAttribArray(1)
        glVertexAttribPointer(2, 3, GL_FLOAT, False, 9 * 4, ctypes.c_void_p(6 * 4))
        glEnableVertexAttribArray(2)

        element_buffer_object = glGenBuffers(1)
        glBindBuffer(GL_ELEMENT_ARRAY_BUFFER, element_buffer_object)
        glBufferData(GL_ELEMENT_ARRAY_BUFFER, faces.nbytes, faces, GL_STATIC_DRAW)

        glUniformMatrix4fv(
            glGetUniformLocation(shader, "model"), 1 , GL_FALSE, 
            model
        )
        glUniformMatrix4fv(
            glGetUniformLocation(shader, "view"), 1 , GL_FALSE, 
            glm.value_ptr(view)
        )
        glUniformMatrix4fv(
            glGetUniformLocation(shader, "projection"), 1 , GL_FALSE, 
            glm.value_ptr(projection)
        )

        diffuse = mesh.material.properties["diffuse"]

        if difuse == False:
            glUniform4f(
                glGetUniformLocation(shader, "color"),
                *diffuse,
                1
            )
        else:
            glUniform4f(
                glGetUniformLocation(shader, "color"),
                0.1,0.8,0.3,
                1
            )
            
        glUniform4f(
            glGetUniformLocation(shader, "light"), 
            light.w, light.x, light.y, 1
        )

        glDrawElements(GL_TRIANGLES, len(faces), GL_UNSIGNED_INT, None)


    for child in node.children:
        glize(child, light, recTexture, difuse)

camera = glm.vec3(0, 0, -100) #Vista de camara

################################################################################
#                             SET-UP DE CONTROLES                              #
################################################################################
def process_input(coordX, coordY, radius, light, texture, difuse):
    for event in pygame.event.get():

        if event.type == pygame.KEYUP and event.key == pygame.K_ESCAPE:
            exit()
        if event.type == pygame.KEYDOWN:
            #DERECHA-IZQUIERDA
            if event.key == pygame.K_a: #a - izquierda
                coordX = coordX - 6
                camera.x = radius * math.cos(math.radians(coordX))
                camera.z = radius * math.sin(math.radians(coordX))

            if event.key == pygame.K_d: #d- derecha
                coordX = coordX + 12
                camera.x = radius * math.cos(math.radians(coordX))
                camera.z = radius * math.sin(math.radians(coordX))

            if event.key == pygame.K_z: #DISMINUCION RADIO.
                if radio >= 25:
                    radio = radius - 12
                    camera.x = radius * math.cos(math.radians(coordX))
                    camera.z = radius * math.sin(math.radians(coordX))
                else:
                    pass

            #AUMENTO RADIO    
            if event.key == pygame.K_r:
                if radio <= 150:
                    radio = radius + 12
                    camera.x = radius * math.cos(math.radians(coordX))
                    camera.z = radius * math.sin(math.radians(coordX))
                else:
                    pass

            #ARRIBA-ABAJO    
            if event.key == pygame.K_w: 
                if coordY >= 0:
                    coordY = coordY - 12
                    camera.y = radius * math.cos(math.radians(coordY))
                else:
                    pass
                
            if event.key == pygame.K_s:
                if coordY <= 50:
                    coordY = coordY + 12
                    camera.y = radius * math.cos(math.radians(coordY))
                else:
                    pass
            if event.key == pygame.K_m:
                light.x = light.x * -2
            if event.key == pygame.K_n:
                light.y = light.y * -2
            if event.key == pygame.K_l:
                glPolygonMode(GL_FRONT_AND_BACK, GL_FILL)
            if event.key == pygame.K_k:
                glPolygonMode(GL_FRONT_AND_BACK, GL_LINE)

            if event.key == pygame.K_p:#TEXTURIZAR.
                if texture == False:
                    texture = True
                else:
                    texture = False

            if event.key == pygame.K_o:#REALIZAR DIFUSION.
                if difuse == False:
                    difuse = True
                else:
                    difuse = False
    return coordX, coordY, radius, light, texture, difuse
################################################################################

################################################################################
#                             NUEVAS VARIABLES                                 #
################################################################################
newRadius = 100
newCoordX = 0.0
newCoordY = 0.0

newLight = glm.vec4(300, 300, 300 , 1)

newTexture = False
newDifuse = False
################################################################################

while True: #Ciclo de despliegue de pantalla.
    glClear(GL_COLOR_BUFFER_BIT|GL_DEPTH_BUFFER_BIT) #Actualizacion.
    
    view = glm.lookAt(camera, glm.vec3(0, 0, 0), glm.vec3(0, 1, 0)) #Vista de camara.   

    glize(scene.rootnode, newLight, newTexture, newDifuse) #Llamada a Glize

    newCoordX, newCoordY, newRadius, newLight, newTexture, newDifuse = process_input(newCoordX, newCoordY, newRadius, newLight, newTexture, newDifuse) #Entrada de valores a variables.

    clock.tick(15)  
    pygame.display.flip() #Despliegue de pantalla.
