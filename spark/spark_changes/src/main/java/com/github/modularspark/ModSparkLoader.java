/*
 * Licensed to the Apache Software Foundation (ASF) under one or more
 * contributor license agreements.  See the NOTICE file distributed with
 * this work for additional information regarding copyright ownership.
 * The ASF licenses this file to You under the Apache License, Version 2.0
 * (the "License"); you may not use this file except in compliance with
 * the License.  You may obtain a copy of the License at
 *
 *    http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 */
package com.github.modularspark;

import sun.misc.SharedSecrets;
import sun.misc.URLClassPath;

import java.net.URL;
import java.net.URLClassLoader;
import java.util.ArrayList;

public class ModSparkLoader extends URLClassLoader {
    URLClassPath ucp = SharedSecrets.getJavaNetAccess().getURLClassPath(this);
    static {
        ClassLoader.registerAsParallelCapable();
    }
    private final ClassLoader parent;
    public ModSparkLoader(ClassLoader newParent) {
        super(new URL[0], newParent);
        parent = newParent;
        System.out.println("ModSparkLoader called");
    }
//    public URL[] getURLs() {
//        final String paths = System.getProperty("java.class.path");
//        String [] pathList = paths.split(":");
//        URL [] arr;
//        for (
//    }
    public Class<?> loadClass(String className) throws ClassNotFoundException {
        System.out.println("ModSparkLoader loadClass " + className);
        if (!className.contains("spark")) {
            return this.parent.loadClass(className);
        }
        return loadClass(className, true);
    }
    public void addURL(URL urlName) {
        System.out.println("ModSparkLoader addURL " + urlName);
        super.addURL(urlName);
    }
    public Class<?> loadClass(String className, boolean resolve) throws ClassNotFoundException {
        System.out.println("ModSparkLoader loadClass2 " + className);
        // return super.loadClass(className, resolve);
        // if (this.ucp.knownToNotExist(className)) {
        Class var5 = this.findLoadedClass(className);
        if (var5 != null) {
            if (resolve) {
                this.resolveClass(var5);
            }
            return var5;
        } else {
            Class foundClass = super.findClass(className);

            if (foundClass != null) {
                return foundClass;
            } else {
                return super.loadClass(className, resolve);
            }
        }
    }
    public Class<?> findClass(String className) throws ClassNotFoundException {
        System.out.println("ModSparkLoader findClass " + className);
        return super.findClass(className);
    }
}
// public class ModSparkLoader extends ClassLoader {
//    static {
//        ClassLoader.registerAsParallelCapable();
//    }
//    private final ClassLoader parent;
//    public ModSparkLoader(ClassLoader newParent) {
//        super(newParent);
//        parent = newParent;
//        System.out.println("ModSparkLoader called");
//    }
//    public Class<?> loadClass(String className) throws ClassNotFoundException {
//        System.out.println("ModSparkLoader " + className);
//        return this.parent.loadClass(className);
//    }
//}
