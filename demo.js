var canvas,gl,root;
var barFps,barTime,log;
var prog,screenGeom,cursor;
var resScale=1.0;
var countFPS=createFpsCounter();

var hasError=false;

var cameraControl=createFreeLookCameraControl({"pos":[0,0,0],"yaw":0,"pitch":0,"speed":0.01,"slow":0.92,"lookSpeed":0.005});

var viewPos=[0,0,0],viewYawPitch=[0,0];
var mouseLocked=false,moving=[0,0,0];

var getTime=(function(){var start;return (()=>{start=start||Date.now(); return ((Date.now()-start)/1000)%3.402823e+38;});})();


var fixedTimeStep=createFixedTimeStep(1/60,5);

var MyMenu = function() {
    this.bumpMapping=true;
    this.normalMapping=true;
    this.linearFiltering = false;

    this.lightAnimate=true;
    this.lightPosX=0;
    this.lightPosY=0;
    this.lightPosZ=-3;
};

var myMenu = new MyMenu();

function lookRot(yaw,pitch) {
    var sx=Math.sin(pitch);
    var sy=Math.sin(yaw);
    var cx=Math.cos(pitch);
    var cy=Math.cos(yaw);
    return [cy,0,-sy, sy*sx,cx,cy*sx, sy*cx,-sx,cy*cx]; //col major
}

function calcViewPos(pos,rot,move) {
    pos[0]+=rot[6]*move[2] +rot[0]*move[0];
    pos[1]+=rot[7]*move[2]+rot[1]*move[0];
    pos[2]+=rot[8]*move[2]+rot[2]*move[0];
}

function setErrorMsg(msg) {
    root.innerHTML=hasError?root.innerHTML:'';
    hasError=true;
    root.innerHTML+='<pre>'+msg+'</pre>';
}

function onAnimate() {
    if(hasError) {
        return false;
    }

    var width=Math.floor(canvas.offsetWidth*resScale);
    var height=Math.floor(canvas.offsetHeight*resScale);

    var curTime=getTime();
    
    cameraControl.update();
        
    //
    fixedTimeStep(curTime,(dt)=>{
        cameraControl.step(dt);
    },(it)=>{
        cameraControl.render(it);
    });
    
    var cursor2=[cursor[0]*resScale,cursor[1]*resScale,cursor[2]*resScale,cursor[3]*resScale];

    //var ms=(cursor2[0]==0&&cursor2[1]==0)?[0,0]:[(cursor2[0]/width)*2-1,(cursor2[1]/height)*2-1];

    //canvas.width=width;
    //canvas.height=height;
    
    var viewPos=cameraControl.getPos();
    var viewRot=cameraControl.getRot();

    prog.uniform3fv("viewPos",viewPos);
    prog.uniformMatrix3fv("viewRot",false,viewRot);
    prog.uniform3f("lightPos",myMenu.lightPosX,myMenu.lightPosY,myMenu.lightPosZ);

    prog.uniform3f("iResolution",width,height,0);
    prog.uniform1f("iTime",curTime);
    prog.uniform4fv("iMouse",cursor2);

    prog.uniform1i("useLinearFiltering",myMenu.linearFiltering);
    prog.uniform1i("useBumpMapping",myMenu.bumpMapping);
    prog.uniform1i("useNormalMapping",myMenu.normalMapping);
    prog.uniform1i("lightAnimate",myMenu.lightAnimate);

    screenGeom.draw(width,height);

    if(barFps){barFps.innerHTML = countFPS().toFixed(1) + " fps";}
    if(barTime){barTime.innerHTML = curTime.toFixed(2) ;}

    requestAnimFrame(onAnimate);
}


function registerInputEvents(element) {
    (function(){
        //var lmb=false;

        window.addEventListener("keydown", (function(event){
                cameraControl.keydown(event);
        }));
        
        window.addEventListener("keyup", (function(event){
                cameraControl.keyup(event);
        }));

        element.addEventListener('mousemove', function(event) {
            if(PL.isEnabled() //|| (!PL.isSupported && lmb)
                ) {
                cameraControl.mousemove(event);
            }
        }, false);

        element.addEventListener("mousedown",function(event){
            if(event.button==0){
                //lmb=true;
                //PL.requestPointerLock(element);
                
                if(PL.isEnabled()) {
                    PL.exitPointerLock();
                } else {
                    PL.requestPointerLock(element);
                }
            }
        });

        window.addEventListener("mouseup",function(event){
            //if(event.button==0&&lmb){
            //    lmb=false;
            //    PL.exitPointerLock();
            //}
        });
    })();
}

function printLog(msg){
    var logElement=document.getElementById("log");
    var m=document.createElement('span');
    m.innerHTML=msg;
        
    var e=document.createElement('span');
        
    logElement.appendChild(document.createElement('br'));
    logElement.appendChild(m);
    logElement.appendChild(e);
    return (function(x){e.innerHTML=x;});
};

function initGui() {
    var gui = new dat.GUI();
    gui.add(myMenu, 'linearFiltering');
    //gui.add(myMenu, 'bumpMapping');
    //gui.add(myMenu, 'normalMapping');
    gui.add(myMenu, 'lightAnimate');
    gui.add(myMenu, 'lightPosX', -20, 20).name('lightPosX').step(0.1);;
    gui.add(myMenu, 'lightPosY', -20, 20).name('lightPosY').step(0.1);;
    gui.add(myMenu, 'lightPosZ', -20, 20).name('lightPosZ').step(0.1);;


}

window.onload=(function() {
    log=document.getElementById("log");
    barTime=document.getElementById("barTime");
    barFps=document.getElementById("barFps");
    canvas=document.getElementById("canvas");
    root=document.getElementById("root");
    gl=createGLContext(canvas,{});

    canvas.onselectstart=null;

    registerInputEvents(canvas);

    initGui();
    
    if(!gl) {
        return;
    }

    var useImage=false; //whether to use png or not

    var header="precision highp float;precision highp int;out vec4 outColor;"+
        "uniform vec3 iResolution;uniform float iTime;uniform vec4 iMouse;";

    if(!useImage) {
        header+="uniform highp usampler2D iChannel0;";
    } else {
        header+="uniform sampler2D iChannel0;";
    }

    header+="uniform sampler2D iChannel1;";
    header+="uniform sampler2D iChannel2;";
    header+="uniform vec3 viewPos;uniform mat3 viewRot;";
    header+="uniform vec3 lightPos;";
    header+="uniform bool useLinearFiltering;";
    header+="uniform bool useBumpMapping;";
    header+="uniform bool useNormalMapping;";
    header+="uniform bool lightAnimate;";

    if(useImage) {
        header+="\n#define FROM_IMAGE\n";
    }

    var footer="void main(){mainImage(outColor,gl_FragCoord.xy);}";

    if(!(prog=createProgram(gl,setErrorMsg,header,footer))){
        return;
    }

    prog.use();

    cursor=shadertoyMouseInput(canvas);
    screenGeom=createBindScreenGeometry(gl);

    var resources=[];
    
    var mesh;
    
    var meshLog=printLog("mesh ");
    var shaderLog=printLog("shader ");

    if(!useImage) {
        meshLog("downloading ...");
        
        resources.push(loadBinary("mesh/sibenik.dat",(p)=>{meshLog("downloading : "+(p*100).toFixed(1)+ "%");})
            .then((x)=>{meshLog("decompressing ...");return x;})
            .then((x)=>{return decompressLZMA(x,(p)=>{meshLog("decompressing : "+(p*100).toFixed(1)+ "%");});})
            .then((x)=>{meshLog("ready.");return x;})
        );
    } else {
        meshLog("downloading ...");
        
        resources.push(loadImage("mesh/sibenik.png",(p)=>{meshLog("downloading : "+(p*100).toFixed(1)+ "%");})
            .then((x)=>{meshLog("ready.");return x;})
        );
    }

    shaderLog("downloading ...");
    
    resources.push(loadText("demo.glsl",(p)=>{meshLog("downloading : "+(p*100).toFixed(1)+ "%");})
        .then((x)=>{shaderLog("ready.");return x;}));

    Promise.all(resources).then((result)=>{
        if(!useImage) {
            createBind2dTextureData1UI(gl,0,result[0]);
        } else {
            createBind2dTexture(gl,0,result[0],{mipmap:false,mag_filter:"nearest",min_filter:"nearest",wrap_s:"clamp_to_edge",wrap_t:"clamp_to_edge"});
        }

        if(!prog.set(result[1])) {
            return;
        }

        prog.use();
        prog.uniform1i("iChannel0",0);

    });

    onAnimate();
});


window.onresize=(function(){window.scrollTo(0,0);});

window.requestAnimFrame =
    window.requestAnimationFrame ||
    window.webkitRequestAnimationFrame ||
    window.mozRequestAnimationFrame ||
    window.oRequestAnimationFrame ||
    window.msRequestAnimationFrame ||
    (function(c,e){window.setTimeout(c,1000/60)});

navigator.getUserMedia = navigator.getUserMedia ||
    navigator.webkitGetUserMedia ||
    navigator.mozGetUserMedia;

